"""Tests for the ExpressionEvaluator module."""

import pytest

from models.exceptions import ExpressionError
from utils.expressions import ExpressionEvaluator


class TestExpressionEvaluator:
    """Test cases for ExpressionEvaluator class."""

    def test_simple_template(self):
        """Test simple string template substitution."""
        row_data = {
            "first_name": "John",
            "last_name": "Smith",
        }
        result = ExpressionEvaluator.evaluate("{first_name} {last_name}", row_data)
        assert result == "John Smith"

    def test_template_with_special_chars(self):
        """Test template with special characters."""
        row_data = {
            "email": "test@example.com",
            "domain": "example",
        }
        result = ExpressionEvaluator.evaluate("Email: {email} at {domain}", row_data)
        assert result == "Email: test@example.com at example"

    def test_numeric_comparison_less_than(self):
        """Test numeric comparison (less than)."""
        row_data = {"age": "17"}
        result = ExpressionEvaluator.evaluate("{age} < 18", row_data)
        assert result is True

    def test_numeric_comparison_greater_equal(
        self,
    ):
        """Test numeric comparison (greater than or equal)."""
        row_data = {"age": "25"}
        result = ExpressionEvaluator.evaluate("{age} >= 18", row_data)
        assert result is True

    def test_equality_comparison(self):
        """Test equality comparison."""
        row_data = {"status": "active"}
        result = ExpressionEvaluator.evaluate("{status} == 'active'", row_data)
        assert result is True

    def test_inequality_comparison(self):
        """Test inequality comparison."""
        row_data = {"status": "inactive"}
        result = ExpressionEvaluator.evaluate("{status} != 'active'", row_data)
        assert result is True

    def test_boolean_and(self):
        """Test boolean AND operation."""
        row_data = {"age": "25", "active": "true"}
        result = ExpressionEvaluator.evaluate("{age} >= 18 and {age} < 65", row_data)
        assert result is True

    def test_boolean_or(self):
        """Test boolean OR operation."""
        row_data = {"age": "70"}
        result = ExpressionEvaluator.evaluate("{age} < 18 or {age} >= 65", row_data)
        assert result is True

    def test_arithmetic_addition(self):
        """Test arithmetic addition."""
        row_data = {"price": "100", "tax": "20"}
        result = ExpressionEvaluator.evaluate("{price} + {tax}", row_data)
        assert result == 120

    def test_arithmetic_multiplication(self):
        """Test arithmetic multiplication."""
        row_data = {
            "quantity": "5",
            "price": "10",
        }
        result = ExpressionEvaluator.evaluate("{quantity} * {price}", row_data)
        assert result == 50

    def test_column_not_found(self):
        """Test that missing column raises error."""
        row_data = {"age": "25"}
        with pytest.raises(ExpressionError) as exc_info:
            ExpressionEvaluator.evaluate("{missing_column} > 10", row_data)
        assert "not found in row data" in str(exc_info.value)

    def test_invalid_syntax(self):
        """Test that invalid syntax raises error."""
        row_data = {"age": "25"}
        with pytest.raises(ExpressionError) as exc_info:
            ExpressionEvaluator.evaluate("{age} >>> 10", row_data)
        assert "Invalid expression syntax" in str(exc_info.value)

    def test_unsafe_operation_function_call(self):
        """Test that function calls are rejected."""
        row_data = {"value": "10"}
        # Function calls should be rejected during AST validation
        # We need to use an expression that won't be treated as a simple template
        with pytest.raises(ExpressionError) as exc_info:
            # Using open() with an operator to avoid simple template path
            ExpressionEvaluator.evaluate(
                "open('/etc/passwd') if {value} > 5 else None",
                row_data,
            )
        assert "Unsafe operation" in str(exc_info.value) or "Invalid expression" in str(
            exc_info.value
        )

    def test_is_simple_template(self):
        """Test simple template detection."""
        assert ExpressionEvaluator._is_simple_template("{first} {last}")
        assert ExpressionEvaluator._is_simple_template("Name: {name}")
        assert not ExpressionEvaluator._is_simple_template("{age} > 18")
        assert not ExpressionEvaluator._is_simple_template("{a} + {b}")

    def test_complex_condition(self):
        """Test complex conditional expression."""
        row_data = {"age": "30", "country": "US"}
        result = ExpressionEvaluator.evaluate(
            "({age} >= 18 and {age} < 65) and {country} == 'US'",
            row_data,
        )
        assert result is True

    def test_contains_match(self):
        """Test contains expression when substring is present."""
        row_data = {"os": "windows server 2016"}
        result = ExpressionEvaluator.evaluate("{os} contains '2016'", row_data)
        assert result is True

    def test_contains_no_match(self):
        """Test contains expression when substring is absent."""
        row_data = {"os": "RHEL 7"}
        result = ExpressionEvaluator.evaluate("{os} contains '2016'", row_data)
        assert result is False

    def test_contains_empty_field(self):
        """Test contains expression against an empty field."""
        row_data = {"os": ""}
        result = ExpressionEvaluator.evaluate("{os} contains '2016'", row_data)
        assert result is False

    def test_contains_with_boolean_logic(self):
        """Test contains combined with and/or operators."""
        row_data = {
            "os": "windows server 2016",
            "env": "prod",
        }
        result = ExpressionEvaluator.evaluate(
            "{os} contains 'windows' and {env} == 'prod'",
            row_data,
        )
        assert result is True

    def test_contains_not_a_simple_template(self):
        """Test that contains expressions are not treated as simple templates."""
        assert not ExpressionEvaluator._is_simple_template("{os} contains '2016'")

    def test_contains_quoted_string_with_spaces(
        self,
    ):
        """Test contains with a quoted substring that includes spaces."""
        row_data = {"os": "RHEL 7"}
        assert ExpressionEvaluator.evaluate("{os} contains 'RHEL 7'", row_data) is True
        assert (
            ExpressionEvaluator.evaluate(
                "{os} contains 'Windows Server'",
                row_data,
            )
            is False
        )

    def test_icontains_match(self):
        """Test case-insensitive contains match."""
        row_data = {"os": "Windows Server 2016"}
        assert (
            ExpressionEvaluator.evaluate(
                "{os} icontains 'windows'",
                row_data,
            )
            is True
        )
        assert (
            ExpressionEvaluator.evaluate(
                "{os} icontains 'WINDOWS'",
                row_data,
            )
            is True
        )

    def test_icontains_no_match(self):
        """Test case-insensitive contains non-match."""
        row_data = {"os": "RHEL 7"}
        assert (
            ExpressionEvaluator.evaluate(
                "{os} icontains 'windows'",
                row_data,
            )
            is False
        )

    def test_icontains_with_spaces(self):
        """Test case-insensitive contains with spaces in quoted string."""
        row_data = {"os": "Windows Server 2016"}
        assert (
            ExpressionEvaluator.evaluate(
                "{os} icontains 'windows server'",
                row_data,
            )
            is True
        )

    def test_contains_remains_case_sensitive(
        self,
    ):
        """Test that contains (without i) is still case-sensitive."""
        row_data = {"os": "RHEL 7"}
        assert ExpressionEvaluator.evaluate("{os} contains 'rhel'", row_data) is False
        assert ExpressionEvaluator.evaluate("{os} contains 'RHEL'", row_data) is True

    def test_icontains_not_a_simple_template(
        self,
    ):
        """Test that icontains expressions are not treated as simple templates."""
        assert not ExpressionEvaluator._is_simple_template("{os} icontains 'windows'")
