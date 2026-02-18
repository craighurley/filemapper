"""Safe expression evaluation for FileMapper."""

import ast
import operator
import re
from typing import Any, Dict

from models.exceptions import ExpressionError


class ExpressionEvaluator:
    """Safely evaluates Python expressions with row data context."""

    # Allowed operators for safe evaluation
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.In: lambda left, right: left in right,
        ast.NotIn: lambda left, right: left not in right,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
    }

    # Pattern to rewrite "X contains/icontains Y" before AST parsing.
    # Quoted strings (which may contain spaces) must be matched before \S+.
    _CONTAINS_RE = re.compile(r"""('[^']*'|"[^"]*"|\S+)\s+(i?contains)\s+('[^']*'|"[^"]*"|\S+)""")

    @staticmethod
    def evaluate(expression: str, row_data: Dict[str, Any]) -> Any:
        """
        Safely evaluate an expression with row data as context.

        Supports:
        - Column references: {column_name}
        - Basic arithmetic: +, -, *, /, //, %, **
        - Comparisons: ==, !=, <, <=, >, >=
        - Logical operators: and, or, not
        - String concatenation

        Args:
            expression: The expression to evaluate (e.g., "{age} >= 18")
            row_data: Dictionary of column name to value

        Returns:
            Evaluated result

        Raises:
            ExpressionError: If expression is invalid or unsafe
        """
        try:
            # Check if this is a simple string template (no operators, just {placeholders} and text)
            if ExpressionEvaluator._is_simple_template(expression):
                return ExpressionEvaluator._evaluate_template(expression, row_data)

            # Replace {column_name} with actual values
            prepared_expr = ExpressionEvaluator._prepare_expression(expression, row_data)

            # Parse the expression
            try:
                tree = ast.parse(prepared_expr, mode="eval")
            except SyntaxError as e:
                raise ExpressionError(f"Invalid expression syntax: {e}")

            # Validate the expression is safe
            ExpressionEvaluator._validate_ast(tree)

            # Evaluate the expression
            result = ExpressionEvaluator._eval_node(tree.body)

            return result

        except ExpressionError:
            raise
        except Exception as e:
            raise ExpressionError(f"Failed to evaluate expression '{expression}': {e}")

    @staticmethod
    def _is_simple_template(
        expression: str,
    ) -> bool:
        """
        Check if expression is a simple string template without operators.

        Args:
            expression: The expression to check

        Returns:
            True if it's a simple template, False if it contains operators
        """
        # Remove {placeholders} and check if remaining text contains operators
        pattern = r"\{[^}]+\}"
        without_placeholders = re.sub(pattern, "", expression)

        # If what's left contains any operator symbols, it's not a simple template
        operator_chars = set("+-*/<>=!%&|")
        if any(char in operator_chars for char in without_placeholders):
            return False

        # Check for keyword operators
        keyword_operators = {
            "and",
            "or",
            "not",
            "contains",
            "icontains",
        }
        words = set(without_placeholders.split())
        return not words.intersection(keyword_operators)

    @staticmethod
    def _evaluate_template(expression: str, row_data: Dict[str, Any]) -> str:
        """
        Evaluate a simple string template by substituting placeholders.

        Args:
            expression: Template expression with {column_name} placeholders
            row_data: Row data dictionary

        Returns:
            String with placeholders replaced by values
        """
        pattern = r"\{([^}]+)\}"
        matches = re.findall(pattern, expression)

        result = expression
        for match in matches:
            col_name = match.strip()
            if col_name not in row_data:
                raise ExpressionError(f"Column '{col_name}' not found in row data")

            value = row_data[col_name]
            # Convert value to string for template substitution
            str_value = "" if value is None else str(value)
            result = result.replace(f"{{{col_name}}}", str_value)

        return result

    @staticmethod
    def _prepare_expression(expression: str, row_data: Dict[str, Any]) -> str:
        """
        Replace {column_name} placeholders with Python-safe representations.

        Args:
            expression: Expression with {column_name} placeholders
            row_data: Row data dictionary

        Returns:
            Expression with placeholders replaced
        """
        # Find all {column_name} references
        pattern = r"\{([^}]+)\}"
        matches = re.findall(pattern, expression)

        # Build a mapping of safe variable names
        prepared = expression

        for match in matches:
            col_name = match.strip()
            if col_name not in row_data:
                raise ExpressionError(f"Column '{col_name}' not found in row data")

            value = row_data[col_name]

            # Replace with a Python representation
            if isinstance(value, str):
                # Try to convert to number if it looks numeric
                value_stripped = value.strip()
                if value_stripped:
                    try:
                        # Try integer first
                        if "." not in value_stripped:
                            int_value = int(value_stripped)
                            safe_value = str(int_value)
                        else:
                            # Try float
                            float_value = float(value_stripped)
                            safe_value = str(float_value)
                    except ValueError:
                        # Not a number, treat as string
                        safe_value = repr(value)
                else:
                    safe_value = repr(value)
            elif value is None:
                safe_value = "None"
            else:
                safe_value = str(value)

            prepared = prepared.replace(f"{{{col_name}}}", safe_value)

        # Rewrite "X contains Y" → "Y in X" (case-sensitive)
        # Rewrite "X icontains Y" → "Y_lower in X_lower" (case-insensitive)
        prepared = ExpressionEvaluator._CONTAINS_RE.sub(
            ExpressionEvaluator._rewrite_contains,
            prepared,
        )

        return prepared

    @staticmethod
    def _rewrite_contains(match: re.Match) -> str:
        """Rewrite a contains/icontains match into a Python ``in`` expression."""
        haystack = match.group(1)
        keyword = match.group(2)
        needle = match.group(3)

        if keyword == "icontains":
            # Lowercase both operands for case-insensitive matching
            haystack = ExpressionEvaluator._lower_operand(haystack)
            needle = ExpressionEvaluator._lower_operand(needle)

        return f"{needle} in {haystack}"

    @staticmethod
    def _lower_operand(operand: str) -> str:
        """Lowercase an operand, handling quoted strings."""
        if (operand.startswith("'") and operand.endswith("'")) or (
            operand.startswith('"') and operand.endswith('"')
        ):
            # Lowercase the content inside the quotes
            quote = operand[0]
            return f"{quote}{operand[1:-1].lower()}{quote}"
        # Bare value (already substituted) — lowercase the repr
        try:
            # Numeric values don't need lowering
            float(operand)
            return operand
        except ValueError:
            return operand.lower()

    @staticmethod
    def _validate_ast(tree: ast.AST) -> None:
        """
        Validate that the AST only contains safe operations.

        Args:
            tree: The AST to validate

        Raises:
            ExpressionError: If unsafe operations are detected
        """
        for node in ast.walk(tree):
            # Allow basic expression nodes
            if isinstance(node, (ast.Expression, ast.Load)):
                continue

            # Allow literals (ast.Constant covers all literal types in Python 3.8+)
            if isinstance(node, ast.Constant):
                continue

            # Allow operator nodes themselves (they're checked in their parent nodes)
            if type(node) in ExpressionEvaluator.ALLOWED_OPERATORS:
                continue

            # Allow binary operations with approved operators
            if isinstance(node, ast.BinOp):
                if type(node.op) not in ExpressionEvaluator.ALLOWED_OPERATORS:
                    raise ExpressionError(f"Operator {type(node.op).__name__} not allowed")
                continue

            # Allow unary operations
            if isinstance(node, ast.UnaryOp):
                if type(node.op) not in ExpressionEvaluator.ALLOWED_OPERATORS:
                    raise ExpressionError(f"Operator {type(node.op).__name__} not allowed")
                continue

            # Allow comparison operations
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    if type(op) not in ExpressionEvaluator.ALLOWED_OPERATORS:
                        raise ExpressionError(f"Operator {type(op).__name__} not allowed")
                continue

            # Allow boolean operations
            if isinstance(node, ast.BoolOp):
                if type(node.op) not in ExpressionEvaluator.ALLOWED_OPERATORS:
                    raise ExpressionError(f"Operator {type(node.op).__name__} not allowed")
                continue

            # Reject everything else (function calls, imports, etc.)
            raise ExpressionError(f"Unsafe operation detected: {type(node).__name__}")

    @staticmethod
    def _eval_node(node: ast.AST) -> Any:
        """
        Recursively evaluate an AST node.

        Args:
            node: The AST node to evaluate

        Returns:
            Evaluated result
        """
        # Literals (ast.Constant covers all literal types in Python 3.8+)
        if isinstance(node, ast.Constant):
            return node.value

        # Binary operations
        elif isinstance(node, ast.BinOp):
            left = ExpressionEvaluator._eval_node(node.left)
            right = ExpressionEvaluator._eval_node(node.right)
            op_func = ExpressionEvaluator.ALLOWED_OPERATORS[type(node.op)]
            return op_func(left, right)

        # Unary operations
        elif isinstance(node, ast.UnaryOp):
            operand = ExpressionEvaluator._eval_node(node.operand)
            op_func = ExpressionEvaluator.ALLOWED_OPERATORS[type(node.op)]
            return op_func(operand)

        # Comparison operations
        elif isinstance(node, ast.Compare):
            left = ExpressionEvaluator._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = ExpressionEvaluator._eval_node(comparator)
                op_func = ExpressionEvaluator.ALLOWED_OPERATORS[type(op)]
                if not op_func(left, right):
                    return False
                left = right
            return True

        # Boolean operations
        elif isinstance(node, ast.BoolOp):
            op_func = ExpressionEvaluator.ALLOWED_OPERATORS[type(node.op)]
            values = [ExpressionEvaluator._eval_node(v) for v in node.values]

            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)

        else:
            raise ExpressionError(f"Cannot evaluate node type: {type(node).__name__}")
