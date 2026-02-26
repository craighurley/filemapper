"""Tests for the Mapper module."""

from core.mapper import Mapper
from models.config import (
    Condition,
    Config,
    InputColumn,
    InputSchema,
    MappingRule,
    OutputColumn,
    OutputSchema,
    TypeConversion,
)


class TestMapper:
    """Test cases for Mapper class."""

    def test_map_row_simple_source(self):
        """Test simple source mapping."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="name", type="string")]),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="fullName",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="fullName",
                    source="name",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "name": "John Smith",
            "__row_number__": 1,
        }
        output_row = mapper.map_row(input_row)

        assert output_row["fullName"] == "John Smith"

    def test_map_row_with_expression(self):
        """Test mapping with expression."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="first_name",
                        type="string",
                    ),
                    InputColumn(
                        name="last_name",
                        type="string",
                    ),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="fullName",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="fullName",
                    expression="{first_name} {last_name}",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "first_name": "John",
            "last_name": "Smith",
            "__row_number__": 1,
        }
        output_row = mapper.map_row(input_row)

        assert output_row["fullName"] == "John Smith"

    def test_map_row_with_transform(self):
        """Test mapping with transformation."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="email",
                        type="string",
                    )
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="emailAddress",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="emailAddress",
                    source="email",
                    transform="lowercase",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "email": "TEST@EXAMPLE.COM",
            "__row_number__": 1,
        }
        output_row = mapper.map_row(input_row)

        assert output_row["emailAddress"] == "test@example.com"

    def test_map_row_with_default(self):
        """Test mapping with default value."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="country",
                        type="string",
                        required=False,
                    )
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="region",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="region",
                    source="country",
                    default="UNKNOWN",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "country": "",
            "__row_number__": 1,
        }
        output_row = mapper.map_row(input_row)

        assert output_row["region"] == "UNKNOWN"

    def test_map_row_with_conditions(self):
        """Test mapping with conditional logic."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="age", type="integer")]),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="ageGroup",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="ageGroup",
                    conditions=[
                        Condition(
                            when="{age} < 18",
                            value="Minor",
                        ),
                        Condition(
                            when="{age} >= 18",
                            value="Adult",
                        ),
                    ],
                )
            ],
        )

        mapper = Mapper(config)

        input_row = {
            "age": "15",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["ageGroup"] == "Minor"

        input_row = {
            "age": "25",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["ageGroup"] == "Adult"

    def test_map_row_with_default_condition(self):
        """Test mapping with default condition."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="status",
                        type="string",
                    )
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="statusLabel",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="statusLabel",
                    conditions=[
                        Condition(
                            when="{status} == 'active'",
                            value="Active",
                        ),
                        Condition(
                            is_default=True,
                            value="Unknown",
                        ),
                    ],
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "status": "pending",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["statusLabel"] == "Unknown"

    def test_map_row_boolean_expression(self):
        """Test mapping with boolean expression."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="age", type="integer")]),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="isAdult",
                        type="boolean",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="isAdult",
                    expression="{age} >= 18",
                )
            ],
        )

        mapper = Mapper(config)

        input_row = {
            "age": "25",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["isAdult"] is True

        input_row = {
            "age": "15",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["isAdult"] is False

    def test_map_multiple_rows(self):
        """Test mapping multiple rows."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="name", type="string")]),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="fullName",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="fullName",
                    source="name",
                )
            ],
        )

        mapper = Mapper(config)
        input_rows = [
            {"name": "John", "__row_number__": 1},
            {"name": "Jane", "__row_number__": 2},
        ]
        output_rows = mapper.map_rows(input_rows)

        assert len(output_rows) == 2
        assert output_rows[0]["fullName"] == "John"
        assert output_rows[1]["fullName"] == "Jane"

    # -- value template tests --

    def test_map_row_with_value_template(self):
        """Test value template with field placeholders."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="osName",
                        type="string",
                    ),
                    InputColumn(
                        name="osVersion",
                        type="string",
                    ),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="osInfo",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="osInfo",
                    value="{osName}-{osVersion}",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "osName": "Darwin",
            "osVersion": "24.6.0",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["osInfo"] == "Darwin-24.6.0"

    def test_map_row_with_value_static(self):
        """Test value with no placeholders (static string)."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="dummy",
                        type="string",
                    )
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="greeting",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="greeting",
                    value="Hello World",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "dummy": "test",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["greeting"] == "Hello World"

    def test_map_row_with_value_empty_field(self):
        """Test value template where a referenced field is empty."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="first",
                        type="string",
                    ),
                    InputColumn(
                        name="middle",
                        type="string",
                        required=False,
                    ),
                    InputColumn(name="last", type="string"),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="fullName",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="fullName",
                    value="{first} {middle} {last}",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "first": "John",
            "middle": "",
            "last": "Smith",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["fullName"] == "John  Smith"

    def test_map_row_with_value_complex(self):
        """Test value template with multiple fields and literals."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="firstName",
                        type="string",
                    ),
                    InputColumn(
                        name="lastName",
                        type="string",
                    ),
                    InputColumn(
                        name="email",
                        type="string",
                    ),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="display",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="display",
                    value="{firstName} {lastName} ({email})",
                )
            ],
        )

        mapper = Mapper(config)
        input_row = {
            "firstName": "John",
            "lastName": "Smith",
            "email": "john.smith@example.com",
            "__row_number__": 1,
        }
        assert mapper.map_row(input_row)["display"] == "John Smith (john.smith@example.com)"

    def test_map_row_with_value_from_config_parser_value_key(
        self,
    ):
        """Test value template loaded via ConfigParser using 'value' key."""
        import tempfile
        from pathlib import Path

        from core.config_parser import (
            ConfigParser,
        )

        config_yaml = """
version: "1.0"

input:
  columns:
    - name: osName
      type: string
    - name: osVersion
      type: string

output:
  columns:
    - name: osInfo
      type: string

mappings:
  - output: osInfo
    value: "{osName} - {osVersion}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            mapper = Mapper(config)
            input_row = {
                "osName": "Darwin",
                "osVersion": "24.6.0",
                "__row_number__": 1,
            }
            assert mapper.map_row(input_row)["osInfo"] == "Darwin - 24.6.0"
        finally:
            Path(temp_path).unlink()

    def test_map_row_with_empty_value(self):
        """Test mapping with empty value creates empty column."""
        import tempfile
        from pathlib import Path

        from core.config_parser import (
            ConfigParser,
        )

        config_yaml = """
version: "1.0"

input:
  columns:
    - name: name
      type: string

output:
  columns:
    - name: name
      type: string
    - name: empty_field
      type: string

mappings:
  - output: name
    source: name

  - output: empty_field
    value: ""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            mapper = Mapper(config)
            input_row = {
                "name": "Alice",
                "__row_number__": 1,
            }
            output_row = mapper.map_row(input_row)

            assert output_row["name"] == "Alice"
            assert output_row["empty_field"] == ""
        finally:
            Path(temp_path).unlink()

    # -- condition value with {field} placeholder tests --

    def test_map_row_condition_value_with_field_reference(
        self,
    ):
        """Test condition value containing {field} placeholder resolves from row data."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(name="OSA", type="string"),
                    InputColumn(name="OSB", type="string"),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="osName",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="osName",
                    conditions=[
                        Condition(
                            when="{OSB} == ''",
                            value="{OSA}",
                        ),
                        Condition(
                            is_default=True,
                            value="{OSB}",
                        ),
                    ],
                )
            ],
        )

        mapper = Mapper(config)

        row1 = {
            "OSA": "RHEL 7",
            "OSB": "",
            "__row_number__": 1,
        }
        assert mapper.map_row(row1)["osName"] == "RHEL 7"

        row2 = {
            "OSA": "",
            "OSB": "Windows Server 2016",
            "__row_number__": 2,
        }
        assert mapper.map_row(row2)["osName"] == "Windows Server 2016"

    def test_map_row_condition_value_without_field_reference(
        self,
    ):
        """Test condition value without placeholders remains a static string."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="status",
                        type="string",
                    ),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="label",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="label",
                    conditions=[
                        Condition(
                            when="{status} == 'active'",
                            value="Active",
                        ),
                        Condition(
                            is_default=True,
                            value="Other",
                        ),
                    ],
                )
            ],
        )

        mapper = Mapper(config)
        row = {
            "status": "active",
            "__row_number__": 1,
        }
        assert mapper.map_row(row)["label"] == "Active"

    def test_map_row_condition_value_with_multiple_field_references(
        self,
    ):
        """Test condition value with multiple {field} placeholders."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(
                        name="first",
                        type="string",
                    ),
                    InputColumn(name="last", type="string"),
                    InputColumn(name="role", type="string"),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="display",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="display",
                    conditions=[
                        Condition(
                            when="{role} == 'admin'",
                            value="{first} {last} (Admin)",
                        ),
                        Condition(
                            is_default=True,
                            value="{first} {last}",
                        ),
                    ],
                )
            ],
        )

        mapper = Mapper(config)

        admin = {
            "first": "Jane",
            "last": "Doe",
            "role": "admin",
            "__row_number__": 1,
        }
        assert mapper.map_row(admin)["display"] == "Jane Doe (Admin)"

        user = {
            "first": "John",
            "last": "Smith",
            "role": "user",
            "__row_number__": 2,
        }
        assert mapper.map_row(user)["display"] == "John Smith"

    # -- value template with transform --

    def test_map_row_value_with_transform(self):
        """Test value template followed by a transform."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(name="env", type="string"),
                    InputColumn(name="host", type="string"),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="serverId",
                        type="string",
                    )
                ]
            ),
            mappings=[
                MappingRule(
                    output="serverId",
                    value="{env}-{host}",
                    transform="lowercase",
                )
            ],
        )

        mapper = Mapper(config)
        row = {
            "env": "PROD",
            "host": "Server1",
            "__row_number__": 1,
        }
        assert mapper.map_row(row)["serverId"] == "prod-server1"

    def test_map_row_type_conversion_on_zero(self):
        """Type conversion must not be skipped when result is integer zero."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="count", type="integer")]),
            output_schema=OutputSchema(columns=[OutputColumn(name="countStr", type="string")]),
            mappings=[
                MappingRule(
                    output="countStr",
                    source="count",
                    type_conversion=TypeConversion(from_type="integer", to_type="string"),
                )
            ],
        )
        mapper = Mapper(config)
        result = mapper.map_row({"count": 0, "__row_number__": 1})
        assert result["countStr"] == "0"

    def test_map_row_transform_on_false(self):
        """Transform must not be skipped when result is boolean False."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(columns=[InputColumn(name="age", type="integer")]),
            output_schema=OutputSchema(columns=[OutputColumn(name="isAdult", type="string")]),
            mappings=[
                MappingRule(
                    output="isAdult",
                    expression="{age} >= 18",
                    transform="lowercase",
                )
            ],
        )
        mapper = Mapper(config)
        result = mapper.map_row({"age": "15", "__row_number__": 1})
        assert result["isAdult"] == "false"

    def test_map_row_references_earlier_output(
        self,
    ):
        """Test that a later mapping can reference an earlier output column."""
        config = Config(
            version="1.0",
            input_schema=InputSchema(
                columns=[
                    InputColumn(name="OSA", type="string"),
                    InputColumn(name="OSB", type="string"),
                ]
            ),
            output_schema=OutputSchema(
                columns=[
                    OutputColumn(
                        name="osName",
                        type="string",
                    ),
                    OutputColumn(
                        name="treatment",
                        type="string",
                    ),
                ]
            ),
            mappings=[
                # First: resolve osName from inputs
                MappingRule(
                    output="osName",
                    conditions=[
                        Condition(
                            when="{OSB} == ''",
                            value="{OSA}",
                        ),
                        Condition(
                            is_default=True,
                            value="{OSB}",
                        ),
                    ],
                ),
                # Second: reference the already-mapped osName
                MappingRule(
                    output="treatment",
                    conditions=[
                        Condition(
                            when="{osName} contains '2012'",
                            value="Replatform",
                        ),
                        Condition(
                            is_default=True,
                            value="",
                        ),
                    ],
                ),
            ],
        )

        mapper = Mapper(config)

        # osName resolves to "windows server 2012" → contains '2012' → Replatform
        row1 = {
            "OSA": "windows server 2012",
            "OSB": "windows server 2012",
            "__row_number__": 1,
        }
        out1 = mapper.map_row(row1)
        assert out1["osName"] == "windows server 2012"
        assert out1["treatment"] == "Replatform"

        # osName resolves to "windows server 2016" → no match → empty
        row2 = {
            "OSA": "",
            "OSB": "windows server 2016",
            "__row_number__": 2,
        }
        out2 = mapper.map_row(row2)
        assert out2["osName"] == "windows server 2016"
        assert out2["treatment"] == ""
