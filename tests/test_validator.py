"""Tests for the Validator module."""

from core.validator import Validator
from models.config import InputColumn, InputSchema


class TestValidator:
    """Test cases for Validator class."""

    def test_validate_row_required_field_present(
        self,
    ):
        """Test validation passes when required field is present."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="name",
                    type="string",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "name": "John",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert is_valid
        assert len(errors) == 0

    def test_validate_row_required_field_missing(
        self,
    ):
        """Test validation fails when required field is missing."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="name",
                    type="string",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "other": "value",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert len(errors) == 1
        assert "Required column 'name' is missing" in errors[0]

    def test_validate_row_required_field_empty(
        self,
    ):
        """Test validation fails when required field is empty."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="name",
                    type="string",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {"name": "", "__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert len(errors) == 1

    def test_validate_row_optional_field_missing(
        self,
    ):
        """Test validation passes when optional field is missing."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="nickname",
                    type="string",
                    required=False,
                )
            ]
        )
        validator = Validator(schema)

        row = {"__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert is_valid
        assert len(errors) == 0

    def test_validate_type_integer_valid(self):
        """Test integer type validation with valid value."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {"age": "25", "__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert is_valid
        assert len(errors) == 0

    def test_validate_type_integer_invalid(self):
        """Test integer type validation with invalid value."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "age": "not_a_number",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert "expects integer" in errors[0]

    def test_validate_type_float_valid(self):
        """Test float type validation with valid value."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="price",
                    type="float",
                    required=True,
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "price": "19.99",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert is_valid

    def test_validate_pattern_valid(self):
        """Test pattern validation with matching value."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="email",
                    type="string",
                    required=True,
                    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "email": "test@example.com",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert is_valid

    def test_validate_pattern_invalid(self):
        """Test pattern validation with non-matching value."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="email",
                    type="string",
                    required=True,
                    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                )
            ]
        )
        validator = Validator(schema)

        row = {
            "email": "invalid-email",
            "__row_number__": 1,
        }
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert "does not match required pattern" in errors[0]

    def test_validate_min_max_within_range(self):
        """Test min/max validation with value in range."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                    min=0,
                    max=150,
                )
            ]
        )
        validator = Validator(schema)

        row = {"age": "25", "__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert is_valid

    def test_validate_min_below_minimum(self):
        """Test min validation with value below minimum."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                    min=0,
                    max=150,
                )
            ]
        )
        validator = Validator(schema)

        row = {"age": "-5", "__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert "less than minimum" in errors[0]

    def test_validate_max_above_maximum(self):
        """Test max validation with value above maximum."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                    min=0,
                    max=150,
                )
            ]
        )
        validator = Validator(schema)

        row = {"age": "200", "__row_number__": 1}
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert "greater than maximum" in errors[0]

    def test_validate_multiple_errors(self):
        """Test that multiple validation errors are collected."""
        schema = InputSchema(
            columns=[
                InputColumn(
                    name="name",
                    type="string",
                    required=True,
                ),
                InputColumn(
                    name="age",
                    type="integer",
                    required=True,
                ),
            ]
        )
        validator = Validator(schema)

        row = {"__row_number__": 1}  # Both fields missing
        is_valid, errors = validator.validate_row(row)

        assert not is_valid
        assert len(errors) == 2
