"""Tests for the Transformer module."""

from datetime import datetime

import pytest

from core.transformer import Transformer
from models.exceptions import TransformationError


class TestTransformer:
    """Test cases for Transformer class."""

    def test_apply_transform_uppercase(self):
        """Test uppercase transformation."""
        result = Transformer.apply_transform("hello world", "uppercase")
        assert result == "HELLO WORLD"

    def test_apply_transform_lowercase(self):
        """Test lowercase transformation."""
        result = Transformer.apply_transform("HELLO WORLD", "lowercase")
        assert result == "hello world"

    def test_apply_transform_trim(self):
        """Test trim transformation."""
        result = Transformer.apply_transform("  hello world  ", "trim")
        assert result == "hello world"

    def test_apply_transform_titlecase(self):
        """Test titlecase transformation."""
        result = Transformer.apply_transform("hello world", "titlecase")
        assert result == "Hello World"

    def test_apply_transform_strip_whitespace(
        self,
    ):
        """Test strip_whitespace transformation."""
        result = Transformer.apply_transform("hello  world", "strip_whitespace")
        assert result == "helloworld"

    def test_apply_transform_invalid(self):
        """Test that invalid transformation raises error."""
        with pytest.raises(TransformationError) as exc_info:
            Transformer.apply_transform("test", "invalid_transform")
        assert "Unsupported transformation" in str(exc_info.value)

    def test_convert_type_string_to_integer(self):
        """Test string to integer conversion."""
        result = Transformer.convert_type("123", "string", "integer")
        assert result == 123
        assert isinstance(result, int)

    def test_convert_type_string_to_float(self):
        """Test string to float conversion."""
        result = Transformer.convert_type("123.45", "string", "float")
        assert result == 123.45
        assert isinstance(result, float)

    def test_convert_type_string_to_boolean_true(
        self,
    ):
        """Test string to boolean conversion (true values)."""
        for value in [
            "true",
            "TRUE",
            "1",
            "yes",
            "y",
            "on",
        ]:
            result = Transformer.convert_type(value, "string", "boolean")
            assert result is True

    def test_convert_type_string_to_boolean_false(
        self,
    ):
        """Test string to boolean conversion (false values)."""
        for value in [
            "false",
            "FALSE",
            "0",
            "no",
            "n",
            "off",
        ]:
            result = Transformer.convert_type(value, "string", "boolean")
            assert result is False

    def test_convert_type_string_to_date_with_format(
        self,
    ):
        """Test string to date conversion with format."""
        result = Transformer.convert_type(
            "2024-01-15",
            "string",
            "date",
            "%Y-%m-%d",
        )
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_convert_type_integer_to_string(self):
        """Test integer to string conversion."""
        result = Transformer.convert_type(123, "integer", "string")
        assert result == "123"
        assert isinstance(result, str)

    def test_convert_type_date_to_string_with_format(
        self,
    ):
        """Test date to string conversion with format."""
        date_value = datetime(2024, 1, 15)
        result = Transformer.convert_type(
            date_value,
            "date",
            "string",
            "%Y-%m-%d",
        )
        assert result == "2024-01-15"

    def test_convert_type_empty_value(self):
        """Test that empty values return None."""
        result = Transformer.convert_type("", "string", "integer")
        assert result is None

    def test_convert_type_invalid_conversion(
        self,
    ):
        """Test that invalid type conversion raises error."""
        with pytest.raises(TransformationError):
            Transformer.convert_type(
                "not_a_number",
                "string",
                "integer",
            )

    def test_infer_type(self):
        """Test type inference."""
        assert Transformer.infer_type(True) == "boolean"
        assert Transformer.infer_type(123) == "integer"
        assert Transformer.infer_type(123.45) == "float"
        assert Transformer.infer_type(datetime.now()) == "date"
        assert Transformer.infer_type("hello") == "string"
