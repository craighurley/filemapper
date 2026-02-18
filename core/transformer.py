"""Data transformation functions for FileMapper."""

from datetime import datetime
from typing import Any, Optional

from dateutil import parser as date_parser

from models.exceptions import TransformationError


class Transformer:
    """Handles data transformations and type conversions."""

    # Supported text transformations
    TRANSFORMS = {
        "uppercase": lambda x: str(x).upper(),
        "lowercase": lambda x: str(x).lower(),
        "trim": lambda x: str(x).strip(),
        "titlecase": lambda x: str(x).title(),
        "strip_whitespace": lambda x: "".join(str(x).split()),
    }

    @staticmethod
    def apply_transform(value: Any, transform: str) -> str:
        """
        Apply a text transformation to a value.

        Args:
            value: The value to transform
            transform: The transformation to apply

        Returns:
            Transformed string value

        Raises:
            TransformationError: If transform is not supported
        """
        if transform not in Transformer.TRANSFORMS:
            raise TransformationError(
                f"Unsupported transformation: {transform}. "
                f"Supported: {', '.join(Transformer.TRANSFORMS.keys())}"
            )

        try:
            return Transformer.TRANSFORMS[transform](value)
        except Exception as e:
            raise TransformationError(f"Failed to apply transformation '{transform}': {e}")

    @staticmethod
    def convert_type(
        value: Any,
        from_type: str,
        to_type: str,
        format_str: Optional[str] = None,
    ) -> Any:
        """
        Convert a value from one type to another.

        Args:
            value: The value to convert
            from_type: Source type
            to_type: Target type
            format_str: Format string (for date conversions)

        Returns:
            Converted value

        Raises:
            TransformationError: If conversion fails
        """
        if value is None or value == "":
            return None

        try:
            # String to other types
            if from_type == "string" and to_type == "integer":
                return int(value)

            elif from_type == "string" and to_type == "float":
                return float(value)

            elif from_type == "string" and to_type == "boolean":
                return Transformer._string_to_bool(value)

            elif from_type == "string" and to_type == "date":
                return Transformer._string_to_date(value, format_str)

            # Other types to string
            elif to_type == "string":
                if from_type == "date":
                    return Transformer._date_to_string(value, format_str)
                return str(value)

            # Integer/float conversions
            elif from_type == "integer" and to_type == "float":
                return float(value)

            elif from_type == "float" and to_type == "integer":
                return int(value)

            else:
                raise TransformationError(f"Unsupported type conversion: {from_type} to {to_type}")

        except TransformationError:
            raise
        except Exception as e:
            raise TransformationError(
                f"Failed to convert '{value}' from {from_type} to {to_type}: {e}"
            )

    @staticmethod
    def _string_to_bool(value: str) -> bool:
        """Convert string to boolean."""
        value_lower = str(value).lower().strip()
        if value_lower in (
            "true",
            "1",
            "yes",
            "y",
            "on",
        ):
            return True
        elif value_lower in (
            "false",
            "0",
            "no",
            "n",
            "off",
        ):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean")

    @staticmethod
    def _string_to_date(
        value: str,
        format_str: Optional[str] = None,
    ) -> datetime:
        """Convert string to date."""
        if format_str:
            return datetime.strptime(value, format_str)
        else:
            # Use dateutil for flexible parsing
            return date_parser.parse(value)

    @staticmethod
    def _date_to_string(
        value: Any,
        format_str: Optional[str] = None,
    ) -> str:
        """Convert date to string."""
        if isinstance(value, str):
            # Already a string, possibly from previous conversion
            value = date_parser.parse(value)

        if not isinstance(value, datetime):
            raise ValueError(f"Expected datetime object, got {type(value)}")

        if format_str:
            return value.strftime(format_str)
        else:
            return value.isoformat()

    @staticmethod
    def infer_type(value: Any) -> str:
        """
        Infer the type of a value.

        Args:
            value: The value to check

        Returns:
            Type name as string
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, datetime):
            return "date"
        else:
            return "string"
