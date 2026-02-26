# FileMapper

A CLI tool that maps and transforms CSV files based on YAML configuration. It reads an input CSV, applies configurable mapping rules (column renaming, type conversion, conditional logic, expressions, text transformations), and writes the result to an output CSV.

## Quick Start

```bash
pip install -Ue ".[dev]"
python3 filemapper.py -i input.csv -c config.yaml -o output.csv
```

## Project Structure

The main project structure is as follows:

```
filemapper/
├── filemapper.py              # CLI entry point, argument parsing, orchestration
├── core/                      # Core business logic
│   ├── config_parser.py       # Loads YAML config into typed Config objects
│   ├── csv_reader.py          # Reads CSV, yields row dicts with __row_number__
│   ├── csv_writer.py          # Writes output CSV respecting output schema column order
│   ├── mapper.py              # Applies mapping rules: source, value, expression, conditions
│   ├── transformer.py         # Text transforms and type conversions
│   └── validator.py           # Validates rows against input schema rules
├── models/                    # Data models
│   ├── config.py              # Dataclasses: Config, InputSchema, OutputSchema, MappingRule, etc.
│   └── exceptions.py          # Exception hierarchy rooted at FileMapperError
├── utils/
│   └── expressions.py         # AST-based safe expression evaluator
├── tests/                     # pytest test suite
└── examples/                  # Sample configs and data
```

## Architecture

### Data Flow

```
YAML Config File ─→ ConfigParser ─→ Config object
                                        │
Input CSV ─→ CSVReader ─→ row dicts ─→ Validator ─→ Mapper ─→ CSVWriter ─→ Output CSV
                                                       │
                                           ┌───────────┼───────────┐
                                      Transformer  ExpressionEval  Conditions
```

### Processing Pipeline

1. **ConfigParser** loads YAML, validates structure, returns a `Config` dataclass
2. **CSVReader** reads the input file row-by-row as dictionaries (injects `__row_number__` for error context)
3. **Validator** checks each row against `InputSchema` rules (required fields, types, patterns, min/max ranges)
4. **Mapper** applies each `MappingRule` to produce output rows — delegates to Transformer/ExpressionEvaluator as needed
5. **CSVWriter** writes output rows respecting `OutputSchema` column ordering

### Key Design Decisions

- **Row-by-row streaming** for memory efficiency on large files
- **Unified `{field}` template resolution** — a single `_resolve_template()` method resolves `{field}` placeholders everywhere: `value`, condition `value`, and `default` fields
- **AST-validated expression evaluation** — parses expressions into an AST, whitelists only safe operators (arithmetic, comparison, boolean), blocks function calls/imports/attribute access
- **Error collection** — validation and mapping errors are accumulated per row; `--strict` mode fails on first error
- **Configuration-time validation** — catches invalid configs (missing columns, unmapped outputs, invalid template references) before any data processing begins

## Data Models (`models/config.py`)

All models are Python `dataclass` objects:

| Model | Purpose |
| --- | --- |
| `Config` | Top-level: version, input_schema, output_schema, mappings list |
| `InputSchema` | List of `InputColumn` definitions |
| `OutputSchema` | List of `OutputColumn` definitions |
| `InputColumn` | name, type, required, pattern (regex), min, max |
| `OutputColumn` | name, type |
| `MappingRule` | output, source, expression, value, transform, default, type_conversion, conditions |
| `TypeConversion` | from_type, to_type, format |
| `Condition` | when (expression), value (template string), is_default (bool) |

`Config.validate()` cross-checks that all mapping sources exist in the input schema, all `{field}` references in `value` templates resolve to valid input columns, and all output columns have a corresponding mapping.

## Exception Hierarchy (`models/exceptions.py`)

```
FileMapperError (base)
├── ConfigurationError    # Invalid YAML or config structure
├── ValidationError       # Input data fails schema rules (carries .errors list)
├── MappingError          # Mapping rule execution failure
├── TransformationError   # Type conversion or text transform failure
└── ExpressionError       # Unsafe or invalid expression
```

## YAML Configuration Format

Every config file requires four top-level keys: `version`, `input`, `output`, `mappings`.

### Input Schema

Defines expected input columns with optional validation rules:

```yaml
input:
  columns:
    - name: age
      type: integer        # string | integer | float | boolean | date
      required: true
      min: 0               # numeric range (optional)
      max: 150
    - name: email
      type: string
      required: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"  # regex (optional)
```

### Output Schema

Defines the output column names and order:

```yaml
output:
  columns:
    - name: fullName
      type: string
    - name: ageGroup
      type: string
```

### Mapping Rules

Each rule maps one output column. Exactly one of `source`, `expression`, `value`, or `conditions` is required.

All string outputs support `{field}` template placeholders resolved against the input row. This applies uniformly to `value`, condition `value`, and `default` fields.

**Simple source mapping** — copy a column (optionally rename):

```yaml
- output: firstName
  source: first_name
```

**With text transformation** — applied after value resolution:

```yaml
- output: email
  source: email
  transform: lowercase    # uppercase | lowercase | trim | titlecase | strip_whitespace
```

**Value template** — build output from `{field}` placeholders and literal text:

```yaml
- output: fullName
  value: "{first_name} {last_name}"
```

A `value` can also be a static string with no placeholders, or an empty string `""` to produce a blank column.

**Expression** — safe Python expression with `{field}` references, returns a computed result:

```yaml
- output: isAdult
  expression: "{age} >= 18"
```

Numeric strings in `{field}` references are auto-converted for arithmetic/comparison. Non-numeric strings are quoted. Supported operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `and`, `or`, `not`, `contains`, `icontains`.

**String containment** — check if a field's value contains a substring. `contains` is case-sensitive, `icontains` is case-insensitive:

```yaml
- output: osType
  conditions:
    - when: "{osName} icontains 'windows'"
      value: "Windows"
    - when: "{osName} icontains 'rhel'"
      value: "Nix"
    - default: ""
```

Both are rewritten to Python's `in` operator internally. `icontains` lowercases both operands before comparison. They can be combined with `and`/`or` for compound checks.

**Conditional logic** — first matching `when` wins; `default` is the fallback. Both static strings and `{field}` templates are supported in `value`:

```yaml
# Static values
- output: ageGroup
  conditions:
    - when: "{age} < 18"
      value: "Minor"
    - when: "{age} >= 18 and {age} < 65"
      value: "Adult"
    - default: "Unknown"

# Dynamic values — select column data based on a condition
- output: osName
  conditions:
    - when: "{X} == ''"
      value: "{Y}"
    - default: "{X}"
```

**Type conversion** — convert between types with optional format string:

```yaml
- output: registrationDate
  source: signup_date
  type_conversion:
    from: string
    to: date
    format: "%Y-%m-%d"
```

Supported conversions: string ↔ integer, string ↔ float, string ↔ boolean (`true/false/1/0/yes/no/y/n/on/off`), string ↔ date (uses `dateutil` for flexible parsing when no format given), integer ↔ float, date → string.

**Default value** — used when source/value resolves to empty/None. Also supports `{field}` templates:

```yaml
- output: region
  source: country_code
  default: "UNKNOWN"
  transform: uppercase
```

### Rule Application Order

Within a single mapping rule, the operations apply in this order:

1. Resolve value (source / value / expression / conditions)
2. Apply default if value is empty (with template resolution)
3. Apply text transformation
4. Apply type conversion

## CLI Interface

```
python3 filemapper.py [options]

Required:
  -i, --input FILE        Input CSV file
  -c, --config FILE       YAML configuration file
  -o, --output FILE       Output CSV file (required unless --validate-only)

Modes:
  --validate-only         Validate input data and exit
  --strict                Fail immediately on first validation or mapping error

Options:
  --encoding ENCODING     File encoding (default: utf-8)
  --delimiter DELIM       CSV delimiter (default: ,)
```

Exit codes: 0 = success, 1 = error, 130 = keyboard interrupt.

## Expression Evaluator (`utils/expressions.py`)

The `ExpressionEvaluator` uses Python's `ast` module to safely evaluate expressions:

1. **Simple templates** (no operators) — direct string substitution: `"{first_name} {last_name}"` → `"John Smith"`
2. **Operator expressions** — parsed to AST, validated against whitelist, then evaluated node-by-node
3. **Security** — blocks `Call`, `Attribute`, `Import`, `Name` and all other AST node types not explicitly whitelisted

Numeric string values from CSV are auto-converted to int/float for comparisons.

## Development

### Commands

This project uses Taskfile instead of Make.

```bash
# Format
task format

# Lint
task lint

# Run tests
task test
```

### Conventions

- Python 3.13, type hints throughout
- British English spelling in code, comments, and output
- All public methods have docstrings
- Dataclasses with `from_dict()` class methods for deserialisation
- `__row_number__` injected into row dicts for contextual error messages

## Example

The `examples/` directory contains the following files:

Input file: `examples/input.csv`
Configuration file: `examples/config.yaml`
Output file: `examples/output.csv`

The output file was created by running this command: `python filemapper.py -i ./examples/input.csv -c ./examples/config.yaml -o ./examples/output.csv`
