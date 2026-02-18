"""Tests for the CSVWriter module."""

import csv

import pytest

from core.csv_writer import CSVWriter
from models.config import (
    OutputColumn,
    OutputSchema,
)
from models.exceptions import FileMapperError


class TestCSVWriter:
    """Test cases for CSVWriter class."""

    def test_write_basic_rows(self, tmp_path):
        """Test writing basic rows to CSV file."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
                OutputColumn(name="email", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {
                "name": "Alice",
                "age": 30,
                "email": "alice@example.com",
            },
            {
                "name": "Bob",
                "age": 25,
                "email": "bob@example.com",
            },
        ]
        writer.write_rows(rows)

        # Verify file was created and contains correct data
        assert output_file.exists()
        with open(output_file, "r") as f:
            content = f.read()
            assert "name,age,email" in content
            assert "Alice,30,alice@example.com" in content
            assert "Bob,25,bob@example.com" in content

    def test_write_rows_field_order_matches_schema(self, tmp_path):
        """Test that output field order matches schema, not input order."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="email", type="string"),
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        # Input has different field order
        rows = [
            {
                "name": "Alice",
                "age": 30,
                "email": "alice@example.com",
            }
        ]
        writer.write_rows(rows)

        # Read back and verify order
        with open(output_file, "r") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == [
                "email",
                "name",
                "age",
            ]
            data_row = next(reader)
            assert data_row == [
                "alice@example.com",
                "Alice",
                "30",
            ]

    def test_write_rows_with_custom_delimiter(self, tmp_path):
        """Test writing CSV with custom delimiter."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(
            str(output_file),
            schema,
            delimiter=";",
        )
        rows = [{"name": "Alice", "age": 30}]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            content = f.read()
            assert "name;age" in content
            assert "Alice;30" in content

    def test_write_rows_with_custom_encoding(self, tmp_path):
        """Test writing CSV with custom encoding."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="city", type="string"),
            ]
        )

        writer = CSVWriter(
            str(output_file),
            schema,
            encoding="utf-16",
        )
        rows = [{"name": "Alice", "city": "Zürich"}]
        writer.write_rows(rows)

        # Read back with same encoding
        with open(output_file, "r", encoding="utf-16") as f:
            content = f.read()
            assert "Alice" in content
            assert "Zürich" in content

    def test_write_rows_with_none_values(self, tmp_path):
        """Test that None values are written as empty strings."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [{"name": "Alice", "age": None}]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert lines[1].strip() == "Alice,"

    def test_write_rows_with_boolean_values(self, tmp_path):
        """Test that boolean values are formatted correctly."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="active", type="boolean"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {"name": "Alice", "active": True},
            {"name": "Bob", "active": False},
        ]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            content = f.read()
            assert "Alice,True" in content
            assert "Bob,False" in content

    def test_write_rows_with_numeric_values(self, tmp_path):
        """Test that numeric values are formatted correctly."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
                OutputColumn(name="score", type="float"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {
                "name": "Alice",
                "age": 30,
                "score": 95.5,
            }
        ]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            content = f.read()
            assert "Alice,30,95.5" in content

    def test_write_rows_ignores_extra_fields(self, tmp_path):
        """Test that extra fields not in schema are ignored."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {
                "name": "Alice",
                "age": 30,
                "extra_field": "ignored",
                "another": "also ignored",
            }
        ]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ["name", "age"]
            assert "extra_field" not in headers
            assert "another" not in headers

    def test_write_rows_with_missing_fields(self, tmp_path):
        """Test that missing fields are written as empty strings."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
                OutputColumn(name="email", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [{"name": "Alice"}]  # Missing age and email
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert lines[1].strip() == "Alice,,"

    def test_write_empty_rows_list(self, tmp_path):
        """Test writing empty list of rows."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        writer.write_rows([])

        # Should still create file with headers
        assert output_file.exists()
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            assert "name" in lines[0]

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        output_file = tmp_path / "subdir" / "nested" / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [{"name": "Alice"}]
        writer.write_rows(rows)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_write_single_row_create_mode(self, tmp_path):
        """Test writing single row in create mode."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        writer.write_row({"name": "Alice", "age": 30}, mode="w")

        assert output_file.exists()
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2  # Header + 1 row
            assert "name,age" in lines[0]
            assert "Alice,30" in lines[1]

    def test_write_single_row_append_mode(self, tmp_path):
        """Test writing single row in append mode."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)

        # Write first row (creates file)
        writer.write_row({"name": "Alice"}, mode="w")

        # Append second row
        writer.write_row({"name": "Bob"}, mode="a")

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 3  # Header + 2 rows
            assert "Alice" in lines[1]
            assert "Bob" in lines[2]

    def test_write_single_row_creates_header_if_not_exists(self, tmp_path):
        """Test that write_row creates header if file doesn't exist."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        writer.write_row({"name": "Alice"}, mode="a")

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert "name" in lines[0]

    def test_write_rows_with_unicode(self, tmp_path):
        """Test writing rows with Unicode characters."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="city", type="string"),
                OutputColumn(name="emoji", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {
                "name": "Alice",
                "city": "Zürich",
                "emoji": "😀",
            },
            {
                "name": "José",
                "city": "São Paulo",
                "emoji": "🇧🇷",
            },
        ]
        writer.write_rows(rows)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Zürich" in content
            assert "José" in content
            assert "São Paulo" in content
            assert "😀" in content
            assert "🇧🇷" in content

    def test_write_rows_with_special_characters(self, tmp_path):
        """Test writing rows with special characters requiring quoting."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(
                    name="description",
                    type="string",
                ),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [
            {
                "name": "Alice",
                "description": 'Developer, "Senior"',
            },
            {
                "name": "Bob",
                "description": "Manager\nLeader",
            },
        ]
        writer.write_rows(rows)

        # Read back to verify CSV quoting handled correctly
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows_read = list(reader)

        assert rows_read[0]["description"] == 'Developer, "Senior"'
        assert rows_read[1]["description"] == "Manager\nLeader"

    def test_write_error_permission_denied(self, tmp_path):
        """Test error handling when file cannot be written."""
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)
        readonly_file = readonly_dir / "output.csv"

        writer = CSVWriter(str(readonly_file), schema)
        rows = [{"name": "Alice"}]

        try:
            with pytest.raises(FileMapperError) as exc_info:
                writer.write_rows(rows)
            assert "Failed to write output file" in str(exc_info.value)
        finally:
            # Cleanup: restore permissions
            readonly_dir.chmod(0o755)

    def test_write_rows_with_date_objects(self, tmp_path):
        """Test writing rows with various object types as strings."""
        from datetime import datetime

        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
                OutputColumn(name="date", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        date_obj = datetime(2024, 1, 15, 10, 30)
        rows = [{"name": "Alice", "date": date_obj}]
        writer.write_rows(rows)

        with open(output_file, "r") as f:
            content = f.read()
            # Date should be converted to string
            assert "Alice" in content
            assert "2024" in content

    def test_fieldnames_extracted_from_schema(self, tmp_path):
        """Test that fieldnames are correctly extracted from schema."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(
                    name="first_name",
                    type="string",
                ),
                OutputColumn(
                    name="last_name",
                    type="string",
                ),
                OutputColumn(name="age", type="integer"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)

        assert writer.fieldnames == [
            "first_name",
            "last_name",
            "age",
        ]

    def test_write_rows_large_dataset(self, tmp_path):
        """Test writing large number of rows."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="id", type="integer"),
                OutputColumn(name="value", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)
        rows = [{"id": i, "value": f"value_{i}"} for i in range(1000)]
        writer.write_rows(rows)

        # Verify file has correct number of rows
        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1001  # Header + 1000 rows

    def test_write_row_streaming_multiple(self, tmp_path):
        """Test streaming write of multiple rows one at a time."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="name", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)

        # Write rows one at a time
        writer.write_row({"name": "Alice"}, mode="w")
        writer.write_row({"name": "Bob"}, mode="a")
        writer.write_row({"name": "Charlie"}, mode="a")

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 4  # Header + 3 rows
            assert "Alice" in lines[1]
            assert "Bob" in lines[2]
            assert "Charlie" in lines[3]

    def test_format_row_converts_all_types_to_strings(self, tmp_path):
        """Test that _format_row correctly converts all value types."""
        output_file = tmp_path / "output.csv"
        schema = OutputSchema(
            columns=[
                OutputColumn(name="str_val", type="string"),
                OutputColumn(name="int_val", type="integer"),
                OutputColumn(name="float_val", type="float"),
                OutputColumn(
                    name="bool_val",
                    type="boolean",
                ),
                OutputColumn(name="none_val", type="string"),
            ]
        )

        writer = CSVWriter(str(output_file), schema)

        formatted = writer._format_row(
            {
                "str_val": "hello",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": True,
                "none_val": None,
            }
        )

        assert formatted["str_val"] == "hello"
        assert formatted["int_val"] == "42"
        assert formatted["float_val"] == "3.14"
        assert formatted["bool_val"] == "True"
        assert formatted["none_val"] == ""
        # All values should be strings
        assert all(isinstance(v, str) for v in formatted.values())
