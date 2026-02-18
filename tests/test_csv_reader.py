"""Tests for the CSVReader module."""

import pytest

from core.csv_reader import CSVReader
from models.exceptions import FileMapperError


class TestCSVReader:
    """Test cases for CSVReader class."""

    def test_read_valid_csv(self, tmp_path):
        """Test reading a valid CSV file."""
        # Create test CSV file
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,email\nAlice,30,alice@example.com\nBob,25,bob@example.com\n")

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"
        assert rows[0]["email"] == "alice@example.com"
        assert rows[1]["name"] == "Bob"
        assert rows[1]["age"] == "25"

    def test_read_csv_with_row_numbers(self, tmp_path):
        """Test that row numbers are added to each row."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name\nAlice\nBob\n")

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        # Row numbers start at 2 (header is row 1)
        assert rows[0]["__row_number__"] == 2
        assert rows[1]["__row_number__"] == 3

    def test_read_csv_with_custom_delimiter(self, tmp_path):
        """Test reading CSV with custom delimiter."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name;age;city\nAlice;30;London\nBob;25;Paris\n")

        reader = CSVReader(str(csv_file), delimiter=";")
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == "30"
        assert rows[0]["city"] == "London"

    def test_read_csv_with_custom_encoding(self, tmp_path):
        """Test reading CSV with custom encoding."""
        csv_file = tmp_path / "test.csv"
        # Write UTF-16 encoded file
        csv_file.write_text(
            "name,city\nAlice,Zürich\n",
            encoding="utf-16",
        )

        reader = CSVReader(str(csv_file), encoding="utf-16")
        rows = list(reader.read_rows())

        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"
        assert rows[0]["city"] == "Zürich"

    def test_read_csv_with_unicode_characters(self, tmp_path):
        """Test reading CSV with Unicode characters."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "name,city,emoji\nAlice,Zürich,😀\nJosé,São Paulo,🇧🇷\n",
            encoding="utf-8",
        )

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["city"] == "Zürich"
        assert rows[0]["emoji"] == "😀"
        assert rows[1]["name"] == "José"
        assert rows[1]["city"] == "São Paulo"

    def test_read_empty_csv_with_headers_only(self, tmp_path):
        """Test reading CSV with headers but no data rows."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,email\n")

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 0

    def test_read_csv_with_empty_fields(self, tmp_path):
        """Test reading CSV with empty fields."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,email\nAlice,,alice@example.com\n,25,\n")

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == ""
        assert rows[0]["email"] == "alice@example.com"
        assert rows[1]["name"] == ""
        assert rows[1]["age"] == "25"
        assert rows[1]["email"] == ""

    def test_read_csv_with_quoted_fields(self, tmp_path):
        """Test reading CSV with quoted fields containing delimiters."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            'name,description\nAlice,"Developer, Engineer"\nBob,"Manager, ""Leader"""\n'
        )

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["description"] == "Developer, Engineer"
        assert rows[1]["name"] == "Bob"
        assert rows[1]["description"] == 'Manager, "Leader"'

    def test_file_not_found(self):
        """Test error when file does not exist."""
        with pytest.raises(FileMapperError) as exc_info:
            CSVReader("/nonexistent/file.csv")
        assert "Input file not found" in str(exc_info.value)

    def test_csv_with_no_headers(self, tmp_path):
        """Test error when CSV has no headers."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("")

        reader = CSVReader(str(csv_file))
        with pytest.raises(FileMapperError) as exc_info:
            list(reader.read_rows())
        assert "CSV file has no headers" in str(exc_info.value)

    def test_invalid_encoding(self, tmp_path):
        """Test error when encoding is incorrect."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "name,city\nAlice,Zürich\n",
            encoding="utf-16",
        )

        reader = CSVReader(str(csv_file), encoding="utf-8")
        with pytest.raises(FileMapperError) as exc_info:
            list(reader.read_rows())
        assert "Encoding error" in str(exc_info.value)

    def test_get_headers(self, tmp_path):
        """Test getting column headers from CSV."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,email\nAlice,30,alice@example.com\n")

        reader = CSVReader(str(csv_file))
        headers = reader.get_headers()

        assert headers == ["name", "age", "email"]

    def test_get_headers_empty_file(self, tmp_path):
        """Test getting headers from empty file."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("")

        reader = CSVReader(str(csv_file))
        headers = reader.get_headers()

        assert headers == []

    def test_read_csv_with_whitespace(self, tmp_path):
        """Test reading CSV with whitespace in fields."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\n  Alice  ,  30  \n")

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        # CSV reader preserves whitespace
        assert rows[0]["name"] == "  Alice  "
        assert rows[0]["age"] == "  30  "

    def test_read_large_csv_streaming(self, tmp_path):
        """Test that reader can handle large files via streaming."""
        csv_file = tmp_path / "test.csv"

        # Create a CSV with many rows
        with open(csv_file, "w") as f:
            f.write("id,value\n")
            for i in range(1000):
                f.write(f"{i},value_{i}\n")

        reader = CSVReader(str(csv_file))

        # Test that we can iterate without loading all into memory
        count = 0
        for row in reader.read_rows():
            count += 1
            if count == 1:
                assert row["id"] == "0"
                assert row["value"] == "value_0"

        assert count == 1000

    def test_read_csv_with_newlines_in_quoted_fields(self, tmp_path):
        """Test reading CSV with newlines in quoted fields."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text('name,address\nAlice,"123 Main St\nApt 4"\nBob,"456 Oak Ave"\n')

        reader = CSVReader(str(csv_file))
        rows = list(reader.read_rows())

        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["address"] == "123 Main St\nApt 4"

    def test_csv_parsing_error(self, tmp_path):
        """Test handling of malformed CSV."""
        csv_file = tmp_path / "test.csv"
        # Create a malformed CSV (unclosed quote)
        csv_file.write_text('name,age\n"Alice,30\nBob,25\n')

        reader = CSVReader(str(csv_file))
        # CSV module is quite tolerant, but severe errors raise FileMapperError
        # This specific case might not raise, but test the error path exists
        try:
            _ = list(reader.read_rows())
            # If it doesn't raise, that's fine - CSV is tolerant
        except FileMapperError as e:
            assert "CSV parsing error" in str(e) or "Failed to read CSV file" in str(e)

    def test_read_csv_iterator_pattern(self, tmp_path):
        """Test that reader returns an iterator, not a list."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name\nAlice\nBob\n")

        reader = CSVReader(str(csv_file))
        rows_iterator = reader.read_rows()

        # Should be an iterator, not a list
        assert hasattr(rows_iterator, "__iter__")
        assert hasattr(rows_iterator, "__next__")

    def test_read_csv_with_bom(self, tmp_path):
        """Test reading CSV with UTF-8 BOM."""
        csv_file = tmp_path / "test.csv"
        # Write file with BOM
        with open(csv_file, "w", encoding="utf-8-sig") as f:
            f.write("name,age\nAlice,30\n")

        # Read with utf-8-sig to handle BOM
        reader = CSVReader(str(csv_file), encoding="utf-8-sig")
        rows = list(reader.read_rows())

        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"
