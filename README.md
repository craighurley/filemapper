# FileMapper

A CSV transformation tool controlled by YAML configuration. Use this tool to transform, validate,
map, and convert CSV data without writing code.

## Core Capabilities

- **Column mapping**: Rename, copy, or combine columns
- **Data validation**: Type checking, regex patterns, numeric ranges, required fields
- **Transformations**: Text case, trimming, whitespace removal
- **Type conversion**: String ↔ integer, float, boolean, date
- **Conditional logic**: If-then rules with multiple conditions
- **Expressions**: Arithmetic, comparisons, boolean logic
- **String matching**: `contains` and `icontains` (case-insensitive) operators
- **Cross-referencing**: Later mappings can reference already-mapped output columns

## Installation

```bash
pip install -r requirements.txt
```

## Command Reference

### Basic Usage

```bash
# Transform CSV with configuration
python3 filemapper.py -i input.csv -c config.yaml -o output.csv

# Validate input data only
python3 filemapper.py -i input.csv -c config.yaml --validate-only

# Strict mode (fail on first error)
python3 filemapper.py -i input.csv -c config.yaml -o output.csv --strict
```

### All Command Options

| Option                | Required    | Default | Description                                   |
| --------------------- | ----------- | ------- | --------------------------------------------- |
| `-i, --input FILE`    | Yes         | -       | Input CSV file path                           |
| `-c, --config FILE`   | Yes         | -       | YAML configuration file path                  |
| `-o, --output FILE`   | Conditional | -       | Output CSV file path                          |
| `--validate-only`     | No          | false   | Validate input against schema, then exit      |
| `--version`           | No          | -       | Print the version number                      |
| `--strict`            | No          | false   | Stop processing on first validation/map error |
| `--encoding ENCODING` | No          | utf-8   | Character encoding for all files              |
| `--delimiter CHAR`    | No          | `,`     | CSV delimiter character                       |

`--output` is required unless using `--validate-only`

## YAML Configuration Structure

Every configuration file requires exactly four top-level keys: `version`, `input`, `output`,
`mappings`.

### Configuration Skeleton

```yaml
version: "1.0"

input:
  columns:
    - name: column_name
      type: string              # string | integer | float | boolean | date
      required: true            # optional, default: false
      pattern: "regex"          # optional, regex validation
      min: 0                    # optional, numeric minimum
      max: 100                  # optional, numeric maximum

output:
  columns:
    - name: output_column
      type: string

mappings:
  - output: output_column
    source: column_name         # Use ONE of: source, value, expression, or conditions
```

### Input Schema Definition

Define expected columns with validation rules:

```yaml
input:
  columns:
    - name: age                 # Column name in input CSV
      type: integer             # Data type
      required: true            # Validation will fail if missing
      min: 0                    # Numeric range validation
      max: 150
    - name: email
      type: string
      required: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"  # Regex validation
```

**Validation types**: `string`, `integer`, `float`, `boolean`, `date`

**Optional validation rules**:

- `required: true/false` - Field must be present
- `pattern: "regex"` - String must match regex
- `min: number` - Numeric minimum value
- `max: number` - Numeric maximum value

### Output Schema Definition

Define output columns and their order:

```yaml
output:
  columns:
    - name: fullName           # Column name in output CSV
      type: string             # Expected output type
    - name: ageGroup
      type: string
```

Columns appear in output CSV in the order listed here.

## Mapping Rules Reference

Each mapping rule produces **one output column**. Exactly one of these four sources is required:
`source`, `value`, `expression`, or `conditions`.

### 1. Source Mapping (Column Copy/Rename)

Copy a column directly, optionally renaming it:

```yaml
- output: firstName
  source: first_name
```

### 2. Value Templates (String Building)

Build strings using `{field}` placeholders. Placeholders are replaced with input column values:

```yaml
# Combine multiple fields
- output: fullName
  value: "{first_name} {last_name}"

# Static string
- output: status
  value: "Active"

# Mix literals and fields
- output: greeting
  value: "Hello, {first_name}!"
```

### 3. Expressions (Calculations)

Evaluate Python-like expressions with `{field}` references:

```yaml
# Boolean expression
- output: isAdult
  expression: "{age} >= 18"

# Arithmetic
- output: total
  expression: "{price} * {quantity}"

# Complex logic
- output: eligible
  expression: "{age} >= 18 and {score} > 50"
```

**Supported operators**:

- Arithmetic: `+`, `-`, `*`, `/`, `//` (floor division), `%` (modulo), `**` (power)
- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `and`, `or`, `not`
- String matching:
  - `contains` - case-sensitive substring check: `"{name} contains 'Smith'"`
  - `icontains` - case-insensitive substring check: `"{os} icontains 'windows'"`

Numeric strings are auto-converted for arithmetic. Expressions are security-validated (no function
calls, imports, or attribute access allowed).

### 4. Conditional Logic

First matching `when` condition wins. Conditions support both `value` (template strings) and
`expression` (calculations):

```yaml
# Static values based on conditions
- output: ageGroup
  conditions:
    - when: "{age} < 18"
      value: "Minor"
    - when: "{age} >= 18 and {age} < 65"
      value: "Adult"
    - when: "{age} >= 65"
      value: "Senior"
    - default: "Unknown"

# Dynamic values (select different columns based on condition)
- output: primaryOS
  conditions:
    - when: "{X} == ''"
      value: "{Y}"              # Use Y if X is empty
    - default: "{X}"            # Otherwise use X

# String matching
- output: platform
  conditions:
    - when: "{os} contains 'Windows'" # Case sensitive matching
      value: "Windows"
    - when: "{os} icontains 'linux'" # Case insensitive matching
      value: "Linux"
    - default: "Other"

# Expressions in conditions (for calculated outputs)
- output: priorityScore
  conditions:
    - when: "{score} < 10"
      value: "Low"
    - when: "{score} >= 10"
      expression: "{score} * 3"   # Calculate value when condition matches
```

**Important**: Each condition can have either `value` OR `expression`, not both. Use `value` for
static or template strings, `expression` for calculations.

### 5. Text Transformations

Apply after value resolution, before type conversion:

```yaml
- output: email
  source: email_address
  transform: lowercase
```

**Available transforms**:

- `uppercase` - Convert to UPPERCASE
- `lowercase` - Convert to lowercase
- `trim` - Remove leading/trailing whitespace
- `titlecase` - Convert To Title Case
- `strip_whitespace` - Remove all whitespace

### 6. Type Conversions

Convert between data types with optional format strings:

```yaml
# String to date
- output: registrationDate
  source: signup_date
  type_conversion:
    from: string
    to: date
    format: "%Y-%m-%d"

# Date to string
- output: formattedDate
  source: date_field
  type_conversion:
    from: date
    to: string
    format: "%d/%m/%Y"

# String to boolean
- output: isActive
  source: active_flag
  type_conversion:
    from: string
    to: boolean
```

**Supported conversions**:

| From    | To      | Notes                                                            |
| ------- | ------- | ---------------------------------------------------------------- |
| string  | integer | Must be valid integer                                            |
| string  | float   | Must be valid number                                             |
| string  | boolean | Accepts: true/false, 1/0, yes/no, y/n, on/off (case-insensitive) |
| string  | date    | Requires `format` parameter (e.g., "%Y-%m-%d")                   |
| integer | string  | Direct conversion                                                |
| integer | float   | Direct conversion                                                |
| float   | string  | Direct conversion                                                |
| float   | integer | Truncates decimal                                                |
| date    | string  | Requires `format` parameter                                      |
| boolean | string  | Outputs "True" or "False"                                        |

### 7. Default Values

Provide fallback when source/value is empty or None. Supports `{field}` templates:

```yaml
# Static default
- output: region
  source: country_code
  default: "UNKNOWN"
  transform: uppercase

# Dynamic default (use another field)
- output: displayName
  source: nickname
  default: "{first_name}"
```

### 8. Cross-Referencing Output Columns

Later mappings can reference **already-mapped output columns** using `{output_column_name}`:

```yaml
mappings:
  - output: fullName
    value: "{first_name} {last_name}"

  - output: greeting
    value: "Welcome, {fullName}!"    # References the fullName output column
```

This enables multi-stage transformations where one mapping builds on another.

## Mapping Rule Processing Order

Within a single mapping rule, operations apply in this sequence:

1. **Resolve value** (source / value / expression / conditions)
2. **Apply default** if value is empty (with `{field}` template resolution)
3. **Apply text transformation**
4. **Apply type conversion**

## Template Placeholder Rules

Use `{field_name}` to reference columns in:

- `value` fields
- `expression` fields
- `conditions.value` fields
- `default` fields

**Important**: `{field_name}` can reference:

- Input columns (from CSV)
- Already-mapped output columns (earlier in mappings list)

## Example

The `examples/` directory contains the following files:

Input file: `examples/input.csv`
Configuration file: `examples/config.yaml`
Output file: `examples/output.csv`

The output file was created by running this command: `python filemapper.py -i ./examples/input.csv -c ./examples/config.yaml -o ./examples/output.csv`

## Error Handling and Exit Codes

### Error Modes

**Lenient mode (default)**: Collects all errors and continues processing

```bash
python3 filemapper.py -i input.csv -c config.yaml -o output.csv
```

- Validation errors are reported but processing continues
- Mapping errors are reported but successfully mapped rows are written
- Exit code 0 if any rows succeed, 1 if catastrophic failure

**Strict mode**: Stops on first error

```bash
python3 filemapper.py -i input.csv -c config.yaml -o output.csv --strict
```

- Stops immediately on first validation error
- Stops immediately on first mapping error
- Exit code 1 on any error

### Exit Codes

| Code | Meaning                       |
| ---- | ----------------------------- |
| 0    | Success                       |
| 1    | Error (validation or mapping) |
| 130  | Keyboard interrupt (Ctrl+C)   |

### Error Output Format

Validation errors show:

- Row number
- Column name
- Validation rule violated
- Actual value received

Example:

```
✗ Validation failed with 2 error(s):
  - Row 5: Column 'age': Value '200' exceeds maximum (150)
  - Row 8: Column 'email': Value 'invalid' does not match pattern
```

Mapping errors show:

- Row number
- Output column being mapped
- Error description

Example:

```
✗ Mapping failed with 1 error(s):
  - Row 3: Failed to map 'registrationDate': time data '2024-13-45' does not match format '%Y-%m-%d'
```

## Quick Reference for AI Agents

### Decision Tree: Which Mapping Type?

```text
Need to transform CSV data?
│
├─ Copy single column? → Use `source`
│  └─ Example: `source: first_name`
│
├─ Combine multiple columns or add text? → Use `value` template
│  └─ Example: `value: "{first_name} {last_name}"`
│
├─ Calculate or evaluate expression? → Use `expression`
│  └─ Example: `expression: "{price} * {quantity}"`
│
└─ Different outputs based on conditions? → Use `conditions`
   └─ Example:
      conditions:
        - when: "{age} < 18"
          value: "Minor"
        - default: "Adult"
```

### Common Patterns

#### Pattern 1: Rename column

```yaml
- output: newName
  source: oldName
```

#### Pattern 2: Normalise text

```yaml
- output: email
  source: emailAddress
  transform: lowercase
```

#### Pattern 3: Fill missing values

```yaml
- output: country
  source: country_code
  default: "US"
```

#### Pattern 4: Categorise numeric values

```yaml
- output: priceRange
  conditions:
    - when: "{price} < 10"
      value: "Budget"
    - when: "{price} < 50"
      value: "Mid-range"
    - default: "Premium"
```

#### Pattern 5: Combine and transform

```yaml
- output: fullName
  value: "{first_name} {last_name}"
  transform: titlecase
```

#### Pattern 6: Convert date formats

```yaml
- output: formattedDate
  source: raw_date
  type_conversion:
    from: string
    to: date
    format: "%Y-%m-%d"
```

#### Pattern 7: Check if string contains substring

```yaml
- output: osType
  conditions:
    - when: "{operating_system} contains 'Windows'" # Case sensitive matching
      value: "Windows"
    - when: "{operating_system} icontains 'linux'" # Case insensitive matching
      value: "Linux"
    - default: "Other"
```

#### Pattern 8: Reference previously mapped output

```yaml
- output: firstName
  source: first_name

- output: greeting
  value: "Hello, {firstName}!"  # References mapped output, not input
```

#### Pattern 9: Conditional with calculated values

```yaml
- output: adjustedScore
  conditions:
    - when: "{score} < 10"
      value: "Low"
    - when: "{score} >= 10 and {score} < 100"
      expression: "{score} * 2"    # Calculate when in range
    - when: "{score} >= 100"
      expression: "{score} * 1.5"  # Different calculation for high scores
```
