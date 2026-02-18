"""Configuration data models for FileMapper."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Regex for extracting {field} references from template strings
_FIELD_PATTERN = re.compile(r"\{([^}]+)\}")


@dataclass
class InputColumn:
    """Defines an input column with validation rules."""

    name: str
    type: str = "string"
    required: bool = False
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None


@dataclass
class OutputColumn:
    """Defines an output column structure."""

    name: str
    type: str = "string"


@dataclass
class TypeConversion:
    """Defines a type conversion specification."""

    from_type: str
    to_type: str
    format: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TypeConversion":
        """Create TypeConversion from dictionary."""
        return cls(
            from_type=data.get("from", ""),
            to_type=data.get("to", ""),
            format=data.get("format"),
        )


@dataclass
class Condition:
    """Defines a conditional mapping rule.

    A condition can have either a value (template string) or an expression.
    - value: Template string with {field} placeholders (e.g., "{firstName}")
    - expression: Python expression to evaluate (e.g., "{age} * 2")
    """

    when: Optional[str] = None
    value: Optional[str] = None
    expression: Optional[str] = None
    is_default: bool = False

    def __post_init__(self):
        """Validate that value and expression are mutually exclusive."""
        if self.value is not None and self.expression is not None:
            from models.exceptions import (
                ConfigurationError,
            )

            raise ConfigurationError(
                "Condition cannot have both 'value' and 'expression'. Use one or the other."
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        """Create Condition from dictionary."""
        if "default" in data:
            return cls(
                is_default=True,
                value=data["default"],
            )
        return cls(
            when=data.get("when"),
            value=data.get("value"),
            expression=data.get("expression"),
        )


@dataclass
class MappingRule:
    """Defines how an output column is populated from input data.

    Exactly one of source, expression, value, or conditions is required.
    The ``value`` field is a template string supporting {field} placeholders
    (e.g. "{first_name} {last_name}").
    """

    output: str
    source: Optional[str] = None
    expression: Optional[str] = None
    value: Optional[str] = None
    transform: Optional[str] = None
    default: Optional[Any] = None
    type_conversion: Optional[TypeConversion] = None
    conditions: List[Condition] = field(default_factory=list)

    def __post_init__(self):
        """Validate mapping rule after initialisation."""
        if not self.source and not self.expression and self.value is None and not self.conditions:
            from models.exceptions import (
                ConfigurationError,
            )

            raise ConfigurationError(
                f"Mapping for '{self.output}' must have either "
                f"'source', 'expression', 'value', or 'conditions'"
            )


@dataclass
class InputSchema:
    """Defines the structure and validation rules for input CSV."""

    columns: List[InputColumn] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputSchema":
        """Create InputSchema from dictionary."""
        columns = [InputColumn(**col) for col in data.get("columns", [])]
        return cls(columns=columns)


@dataclass
class OutputSchema:
    """Defines the structure for output CSV."""

    columns: List[OutputColumn] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutputSchema":
        """Create OutputSchema from dictionary."""
        columns = [OutputColumn(**col) for col in data.get("columns", [])]
        return cls(columns=columns)


@dataclass
class Config:
    """Overall configuration for FileMapper."""

    version: str
    input_schema: InputSchema
    output_schema: OutputSchema
    mappings: List[MappingRule] = field(default_factory=list)

    def validate(self):
        """Validate the configuration structure."""
        from models.exceptions import (
            ConfigurationError,
        )

        # Get all input and output column names
        input_columns = {col.name for col in self.input_schema.columns}
        output_columns = {col.name for col in self.output_schema.columns}
        mapped_outputs = {mapping.output for mapping in self.mappings}

        # Check that all mappings reference valid output columns
        for mapping in self.mappings:
            if mapping.output not in output_columns:
                raise ConfigurationError(
                    f"Mapping output '{mapping.output}' does not exist in output schema"
                )

            # Check that source columns exist in input schema
            if mapping.source and mapping.source not in input_columns:
                raise ConfigurationError(
                    f"Mapping source '{mapping.source}' does not exist in input schema"
                )

            # Check that {field} references in value templates exist in input schema
            if mapping.value is not None:
                for field_ref in _FIELD_PATTERN.findall(mapping.value):
                    field_ref = field_ref.strip()
                    if field_ref not in input_columns:
                        raise ConfigurationError(
                            f"Value template reference '{{{field_ref}}}' "
                            f"does not exist in input schema"
                        )

        # Check that all output columns are mapped
        unmapped = output_columns - mapped_outputs
        if unmapped:
            raise ConfigurationError(f"Output columns not mapped: {', '.join(unmapped)}")
