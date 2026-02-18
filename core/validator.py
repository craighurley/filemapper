"""Data validation for FileMapper."""

import re
from typing import Any, Dict, List, Tuple

from models.config import InputColumn, InputSchema


class Validator:
    """Validates input data against schema rules."""

    def __init__(self, input_schema: InputSchema):
        """
        Initialise validator with input schema.

        Args:
            input_schema: The input schema to validate against
        """
        self.input_schema = input_schema
        self.columns_by_name = {col.name: col for col in input_schema.columns}

    def validate_row(self, row: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single row against the input schema.

        Args:
            row: Dictionary of column name to value

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        row_num = row.get("__row_number__", "unknown")

        for column in self.input_schema.columns:
            value = row.get(column.name, "").strip() if row.get(column.name) else ""

            # Check required fields
            if column.required and not value:
                errors.append(f"Row {row_num}: Required column '{column.name}' is missing or empty")
                continue

            # Skip validation for empty optional fields
            if not value and not column.required:
                continue

            # Validate type
            type_error = self._validate_type(value, column)
            if type_error:
                errors.append(f"Row {row_num}: {type_error}")
                continue

            # Validate pattern (for strings)
            if column.pattern and column.type == "string":
                if not re.match(column.pattern, value):
                    errors.append(
                        f"Row {row_num}: Column '{column.name}' does not match "
                        f"required pattern: {column.pattern}"
                    )

            # Validate range (for numbers)
            if column.type in (
                "integer",
                "float",
            ):
                try:
                    num_value = float(value)
                    if column.min is not None and num_value < column.min:
                        errors.append(
                            f"Row {row_num}: Column '{column.name}' value {num_value} "
                            f"is less than minimum {column.min}"
                        )
                    if column.max is not None and num_value > column.max:
                        errors.append(
                            f"Row {row_num}: Column '{column.name}' value {num_value} "
                            f"is greater than maximum {column.max}"
                        )
                except ValueError:
                    pass  # Type error already caught above

        is_valid = len(errors) == 0
        return is_valid, errors

    def _validate_type(self, value: str, column: InputColumn) -> str | None:
        """
        Validate that a value matches the expected type.

        Args:
            value: The value to validate
            column: The column definition

        Returns:
            Error message if invalid, None if valid
        """
        if column.type == "string":
            return None  # All values can be strings

        elif column.type == "integer":
            try:
                int(value)
                return None
            except ValueError:
                return f"Column '{column.name}' expects integer, got '{value}'"

        elif column.type == "float":
            try:
                float(value)
                return None
            except ValueError:
                return f"Column '{column.name}' expects float, got '{value}'"

        elif column.type == "boolean":
            value_lower = value.lower().strip()
            if value_lower in (
                "true",
                "false",
                "1",
                "0",
                "yes",
                "no",
                "y",
                "n",
                "on",
                "off",
            ):
                return None
            return f"Column '{column.name}' expects boolean, got '{value}'"

        elif column.type == "date":
            # Basic date format check - actual parsing happens in transformer
            if not value:
                return f"Column '{column.name}' expects date, got empty value"
            return None

        else:
            return f"Unknown type '{column.type}' for column '{column.name}'"

    def validate_all(self, rows: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate multiple rows.

        Args:
            rows: List of row dictionaries

        Returns:
            Tuple of (all_valid, all_error_messages)
        """
        all_errors = []

        for row in rows:
            is_valid, errors = self.validate_row(row)
            all_errors.extend(errors)

        return len(all_errors) == 0, all_errors
