"""CSV file reader for FileMapper."""

import csv
from pathlib import Path
from typing import Any, Dict, Iterator

from models.exceptions import FileMapperError


class CSVReader:
    """Reads CSV files and yields row dictionaries."""

    def __init__(
        self,
        file_path: str,
        encoding: str = "utf-8",
        delimiter: str = ",",
    ):
        """
        Initialise CSV reader.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: CSV delimiter (default: comma)
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.delimiter = delimiter

        if not self.file_path.exists():
            raise FileMapperError(f"Input file not found: {file_path}")

    def read_rows(
        self,
    ) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file and yield row dictionaries.

        Yields:
            Dictionary mapping column names to values for each row

        Raises:
            FileMapperError: If file cannot be read
        """
        try:
            with open(
                self.file_path,
                "r",
                encoding=self.encoding,
                newline="",
            ) as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)

                # Validate that we have headers
                if not reader.fieldnames:
                    raise FileMapperError("CSV file has no headers")

                row_num = 1  # Start at 1 (header is row 0)
                for row in reader:
                    row_num += 1
                    # Add row number for error reporting
                    row["__row_number__"] = row_num
                    yield row

        except csv.Error as e:
            raise FileMapperError(f"CSV parsing error: {e}")
        except UnicodeDecodeError as e:
            raise FileMapperError(
                f"Encoding error (tried {self.encoding}): {e}. Try specifying a different encoding."
            )
        except Exception as e:
            if isinstance(e, FileMapperError):
                raise
            raise FileMapperError(f"Failed to read CSV file: {e}")

    def get_headers(self) -> list:
        """
        Get the column headers from the CSV file.

        Returns:
            List of column names

        Raises:
            FileMapperError: If file cannot be read
        """
        try:
            with open(
                self.file_path,
                "r",
                encoding=self.encoding,
                newline="",
            ) as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                return list(reader.fieldnames or [])
        except Exception as e:
            raise FileMapperError(f"Failed to read CSV headers: {e}")
