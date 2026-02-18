"""CSV file writer for FileMapper."""

import csv
from pathlib import Path
from typing import Any, Dict, List

from models.config import OutputSchema
from models.exceptions import FileMapperError


class CSVWriter:
    """Writes output rows to CSV files."""

    def __init__(
        self,
        file_path: str,
        output_schema: OutputSchema,
        encoding: str = "utf-8",
        delimiter: str = ",",
    ):
        """
        Initialise CSV writer.

        Args:
            file_path: Path where the CSV file will be written
            output_schema: The output schema defining column order
            encoding: File encoding (default: utf-8)
            delimiter: CSV delimiter (default: comma)
        """
        self.file_path = Path(file_path)
        self.output_schema = output_schema
        self.encoding = encoding
        self.delimiter = delimiter
        self.fieldnames = [col.name for col in output_schema.columns]

        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write_rows(self, rows: List[Dict[str, Any]]) -> None:
        """
        Write multiple rows to CSV file.

        Args:
            rows: List of output row dictionaries

        Raises:
            FileMapperError: If file cannot be written
        """
        try:
            with open(
                self.file_path,
                "w",
                encoding=self.encoding,
                newline="",
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=self.fieldnames,
                    delimiter=self.delimiter,
                    extrasaction="ignore",  # Ignore extra fields not in schema
                    lineterminator="\n",
                )

                writer.writeheader()

                for row in rows:
                    # Format values for output
                    formatted_row = self._format_row(row)
                    writer.writerow(formatted_row)

        except IOError as e:
            raise FileMapperError(f"Failed to write output file: {e}")
        except Exception as e:
            if isinstance(e, FileMapperError):
                raise
            raise FileMapperError(f"Error writing CSV: {e}")

    def write_row(self, row: Dict[str, Any], mode: str = "a") -> None:
        """
        Write a single row to CSV file (for streaming).

        Args:
            row: Output row dictionary
            mode: File mode ('w' for new file, 'a' for append)

        Raises:
            FileMapperError: If file cannot be written
        """
        try:
            # Check if we need to write header
            write_header = mode == "w" or not self.file_path.exists()

            with open(
                self.file_path,
                mode,
                encoding=self.encoding,
                newline="",
            ) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=self.fieldnames,
                    delimiter=self.delimiter,
                    extrasaction="ignore",
                    lineterminator="\n",
                )

                if write_header:
                    writer.writeheader()

                formatted_row = self._format_row(row)
                writer.writerow(formatted_row)

        except IOError as e:
            raise FileMapperError(f"Failed to write output file: {e}")
        except Exception as e:
            if isinstance(e, FileMapperError):
                raise
            raise FileMapperError(f"Error writing CSV: {e}")

    def _format_row(self, row: Dict[str, Any]) -> Dict[str, str]:
        """
        Format row values for CSV output.

        Args:
            row: Row dictionary with any value types

        Returns:
            Row dictionary with string values
        """
        formatted = {}

        for field in self.fieldnames:
            value = row.get(field, "")

            # Convert value to string for CSV
            if value is None:
                formatted[field] = ""
            elif isinstance(value, bool):
                # Format booleans consistently
                formatted[field] = str(value)
            elif isinstance(value, (int, float)):
                formatted[field] = str(value)
            else:
                formatted[field] = str(value)

        return formatted
