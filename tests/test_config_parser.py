"""Tests for the ConfigParser module."""

import tempfile
from pathlib import Path

import pytest

from core.config_parser import ConfigParser
from models.exceptions import ConfigurationError


class TestConfigParser:
    """Test cases for ConfigParser class."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: first_name
      type: string
      required: true
    - name: age
      type: integer
      required: false

output:
  columns:
    - name: firstName
      type: string
    - name: age
      type: integer

mappings:
  - output: firstName
    source: first_name
  - output: age
    source: age
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)

            assert config.version == "1.0"
            assert len(config.input_schema.columns) == 2
            assert len(config.output_schema.columns) == 2
            assert len(config.mappings) == 2
        finally:
            Path(temp_path).unlink()

    def test_load_missing_file(self):
        """Test that loading non-existent file raises error."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigParser.load("/non/existent/file.yaml")
        assert "not found" in str(exc_info.value)

    def test_load_invalid_yaml(self):
        """Test that invalid YAML raises error."""
        invalid_yaml = """
invalid: yaml: structure:
  - broken
    indentation
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigParser.load(temp_path)
            assert "Failed to parse YAML" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_missing_version(self):
        """Test that missing version field raises error."""
        config_yaml = """
input:
  columns: []
output:
  columns: []
mappings: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigParser.load(temp_path)
            assert "Missing required field: version" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_unmapped_output_column(self):
        """Test that unmapped output columns raise error."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: first_name
      type: string

output:
  columns:
    - name: firstName
      type: string
    - name: lastName
      type: string

mappings:
  - output: firstName
    source: first_name
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigParser.load(temp_path)
            assert "Output columns not mapped" in str(exc_info.value)
            assert "lastName" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_expression(self):
        """Test loading mapping with expression."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: first_name
      type: string
    - name: last_name
      type: string

output:
  columns:
    - name: fullName
      type: string

mappings:
  - output: fullName
    expression: "{first_name} {last_name}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            assert config.mappings[0].expression == "{first_name} {last_name}"
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_conditions(self):
        """Test loading mapping with conditions."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: age
      type: integer

output:
  columns:
    - name: ageGroup
      type: string

mappings:
  - output: ageGroup
    conditions:
      - when: "{age} < 18"
        value: "Minor"
      - default: "Adult"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            assert len(config.mappings[0].conditions) == 2
            assert config.mappings[0].conditions[0].when == "{age} < 18"
            assert config.mappings[0].conditions[1].is_default
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_type_conversion(
        self,
    ):
        """Test loading mapping with type conversion."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: signup_date
      type: string

output:
  columns:
    - name: registrationDate
      type: date

mappings:
  - output: registrationDate
    source: signup_date
    type_conversion:
      from: string
      to: date
      format: "%Y-%m-%d"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            tc = config.mappings[0].type_conversion
            assert tc is not None
            assert tc.from_type == "string"
            assert tc.to_type == "date"
            assert tc.format == "%Y-%m-%d"
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_value_template(
        self,
    ):
        """Test that 'value' YAML key stores a template string."""
        config_yaml = """
version: "1.0"

input:
  columns:
    - name: first_name
      type: string
    - name: last_name
      type: string

output:
  columns:
    - name: fullName
      type: string

mappings:
  - output: fullName
    value: "{first_name} {last_name}"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            assert config.mappings[0].value == "{first_name} {last_name}"
        finally:
            Path(temp_path).unlink()

    def test_load_mapping_with_empty_value(self):
        """Test loading mapping with empty value string for empty columns."""
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
    - name: empty_column
      type: string

mappings:
  - output: name
    source: name

  - output: empty_column
    value: ""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_yaml)
            temp_path = f.name

        try:
            config = ConfigParser.load(temp_path)
            assert len(config.mappings) == 2
            assert config.mappings[1].output == "empty_column"
            assert config.mappings[1].value == ""
        finally:
            Path(temp_path).unlink()
