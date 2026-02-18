#!/usr/bin/env python3
"""
FileMapper - A CLI tool for mapping and transforming CSV files.
"""

import argparse
import sys

from core.config_parser import ConfigParser
from core.csv_reader import CSVReader
from core.csv_writer import CSVWriter
from core.mapper import Mapper
from core.validator import Validator
from models.exceptions import (
    ConfigurationError,
    FileMapperError,
    MappingError,
    ValidationError,
)


def get_version() -> str:
    """Get the version of the filemapper package."""
    try:
        from importlib.metadata import version

        return version("filemapper")
    except Exception:
        # Fallback for development (package not installed)
        return "0.0.1-dev"


def main():
    """Main entry point for FileMapper CLI."""
    parser = argparse.ArgumentParser(
        description="Map and transform CSV files based on YAML configuration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --version
  %(prog)s --input data.csv --config mapping.yaml --output result.csv
  %(prog)s --input data.csv --config mapping.yaml --validate-only
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input CSV file path",
    )

    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="YAML configuration file path",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output CSV file path (required unless --validate-only)",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate input data, do not perform mapping",
    )

    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding (default: utf-8)",
    )

    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter (default: comma)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on first validation or mapping error",
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.validate_only and not args.output:
        parser.error("--output is required unless --validate-only is specified")

    try:
        # Load configuration
        print(f"Loading configuration from {args.config}...")
        config = ConfigParser.load(args.config)
        print("✓ Configuration loaded successfully")

        # Initialise components
        reader = CSVReader(
            args.input,
            encoding=args.encoding,
            delimiter=args.delimiter,
        )
        validator = Validator(config.input_schema)
        mapper = Mapper(config)

        # Read input rows
        print(f"Reading input from {args.input}...")
        input_rows = list(reader.read_rows())
        print(f"✓ Read {len(input_rows)} rows")

        # Validate input
        print("Validating input data...")
        validation_errors = []
        for row in input_rows:
            is_valid, errors = validator.validate_row(row)
            if not is_valid:
                validation_errors.extend(errors)
                if args.strict:
                    break

        if validation_errors:
            print(f"✗ Validation failed with {len(validation_errors)} error(s):")
            for error in validation_errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(validation_errors) > 10:
                print(f"  ... and {len(validation_errors) - 10} more")

            if args.strict or args.validate_only:
                sys.exit(1)
            else:
                print("Continuing with mapping (use --strict to fail on validation errors)...")
        else:
            print("✓ All rows validated successfully")

        # Exit if validate-only mode
        if args.validate_only:
            print("Validation complete (--validate-only mode)")
            sys.exit(0)

        # Map rows
        print("Mapping rows...")
        output_rows = []
        mapping_errors = []

        for row in input_rows:
            try:
                output_row = mapper.map_row(row)
                output_rows.append(output_row)
            except MappingError as e:
                mapping_errors.append(str(e))
                if args.strict:
                    break

        if mapping_errors:
            print(f"✗ Mapping failed with {len(mapping_errors)} error(s):")
            for error in mapping_errors[:10]:
                print(f"  - {error}")
            if len(mapping_errors) > 10:
                print(f"  ... and {len(mapping_errors) - 10} more")

            if args.strict:
                sys.exit(1)
            else:
                print(f"Continuing with {len(output_rows)} successfully mapped rows...")
        else:
            print(f"✓ Mapped {len(output_rows)} rows successfully")

        # Write output
        print(f"Writing output to {args.output}...")
        writer = CSVWriter(
            args.output,
            config.output_schema,
            encoding=args.encoding,
            delimiter=args.delimiter,
        )
        writer.write_rows(output_rows)
        print(f"✓ Output written successfully to {args.output}")

        print("\n✓ FileMapper completed successfully!")

    except ConfigurationError as e:
        print(
            f"✗ Configuration error: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except ValidationError as e:
        print(
            f"✗ Validation error: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileMapperError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(
            "\n✗ Interrupted by user",
            file=sys.stderr,
        )
        sys.exit(130)
    except Exception as e:
        print(
            f"✗ Unexpected error: {e}",
            file=sys.stderr,
        )
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
