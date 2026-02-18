"""Mapping engine for FileMapper."""

import re
from typing import Any, Dict, List

from core.transformer import Transformer
from models.config import Config, MappingRule
from models.exceptions import (
    ExpressionError,
    MappingError,
    TransformationError,
)
from utils.expressions import ExpressionEvaluator

# Regex for {field} placeholders, compiled once
_FIELD_PATTERN = re.compile(r"\{([^}]+)\}")


class Mapper:
    """Applies mapping rules to transform input rows to output rows."""

    def __init__(self, config: Config):
        """
        Initialise mapper with configuration.

        Args:
            config: The configuration containing mapping rules
        """
        self.config = config
        self.transformer = Transformer()
        self.evaluator = ExpressionEvaluator()

    @staticmethod
    def _resolve_template(template: str, input_row: Dict[str, Any]) -> str:
        """
        Resolve {field} placeholders in a template string against row data.

        Used by ``value``, condition ``value``, and ``default`` fields.
        If the template contains no placeholders it is returned unchanged.

        Args:
            template: String possibly containing {field} references
            input_row: The input row data

        Returns:
            Resolved string value
        """
        if template is None:
            return template

        matches = _FIELD_PATTERN.findall(template)
        if not matches:
            return template

        result = template
        for col_name in matches:
            col_name = col_name.strip()
            raw = input_row.get(col_name)
            replacement = "" if raw is None else str(raw)
            result = result.replace(f"{{{col_name}}}", replacement)

        return result

    def map_row(self, input_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a single input row to an output row.

        Args:
            input_row: Dictionary of input column names to values

        Returns:
            Dictionary of output column names to values

        Raises:
            MappingError: If mapping fails
        """
        output_row = {}
        row_num = input_row.get("__row_number__", "unknown")

        # Combined context: input fields + already-mapped outputs.
        # Later mappings can reference earlier output columns by name.
        row_data = dict(input_row)

        for mapping in self.config.mappings:
            try:
                value = self._apply_mapping(mapping, row_data)
                output_row[mapping.output] = value
                row_data[mapping.output] = value
            except (
                ExpressionError,
                TransformationError,
            ) as e:
                raise MappingError(f"Row {row_num}: {e}")
            except Exception as e:
                raise MappingError(f"Row {row_num}: Failed to map '{mapping.output}': {e}")

        return output_row

    def _apply_mapping(
        self,
        mapping: MappingRule,
        input_row: Dict[str, Any],
    ) -> Any:
        """
        Apply a single mapping rule to get the output value.

        Args:
            mapping: The mapping rule to apply
            input_row: The input row data

        Returns:
            The mapped output value
        """
        result = None

        # Handle conditional mappings
        if mapping.conditions:
            result = self._apply_conditions(mapping, input_row)

        # Handle value template
        elif mapping.value is not None:
            result = self._resolve_template(mapping.value, input_row)

        # Handle expression-based mapping
        elif mapping.expression:
            result = self.evaluator.evaluate(mapping.expression, input_row)

        # Handle simple source mapping
        elif mapping.source:
            result = input_row.get(mapping.source, "")

        # Apply default if result is None or empty
        if (result is None or result == "") and mapping.default is not None:
            result = self._resolve_template(str(mapping.default), input_row)

        # Apply transformation if specified
        if result and mapping.transform:
            result = self.transformer.apply_transform(result, mapping.transform)

        # Apply type conversion if specified
        if result and mapping.type_conversion:
            tc = mapping.type_conversion
            result = self.transformer.convert_type(
                result,
                tc.from_type,
                tc.to_type,
                tc.format,
            )

        return result

    def _apply_conditions(
        self,
        mapping: MappingRule,
        input_row: Dict[str, Any],
    ) -> Any:
        """
        Apply conditional logic to determine output value.

        Condition values support {field} placeholders resolved against
        the input row. Conditions can also use expressions for dynamic
        calculations.

        Args:
            mapping: The mapping rule with conditions
            input_row: The input row data

        Returns:
            The value determined by the first matching condition
        """
        for condition in mapping.conditions:
            if condition.is_default:
                # Default can be a value template or an expression
                if condition.expression:
                    return self.evaluator.evaluate(
                        condition.expression,
                        input_row,
                    )
                return self._resolve_template(condition.value, input_row)

            if condition.when:
                try:
                    result = self.evaluator.evaluate(
                        condition.when,
                        input_row,
                    )
                    if result:
                        # Return expression result or template value
                        if condition.expression:
                            return self.evaluator.evaluate(
                                condition.expression,
                                input_row,
                            )
                        return self._resolve_template(
                            condition.value,
                            input_row,
                        )
                except ExpressionError as e:
                    raise ExpressionError(f"Failed to evaluate condition '{condition.when}': {e}")

    def map_rows(self, input_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map multiple input rows to output rows.

        Args:
            input_rows: List of input row dictionaries

        Returns:
            List of output row dictionaries
        """
        output_rows = []

        for row in input_rows:
            try:
                output_row = self.map_row(row)
                output_rows.append(output_row)
            except MappingError:
                raise

        return output_rows
