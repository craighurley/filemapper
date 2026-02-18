"""Configuration file parser for FileMapper."""

from pathlib import Path
from typing import Any, Dict

import yaml

from models.config import (
    Condition,
    Config,
    InputSchema,
    MappingRule,
    OutputSchema,
    TypeConversion,
)
from models.exceptions import ConfigurationError


class ConfigParser:
    """Parses and validates YAML configuration files."""

    @staticmethod
    def load(config_path: str) -> Config:
        """
        Load and parse a YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Parsed and validated Config object

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        try:
            path = Path(config_path)
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")

            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise ConfigurationError("Configuration file is empty")

            return ConfigParser._parse_config(data)

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML: {e}")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Failed to load configuration: {e}")

    @staticmethod
    def _parse_config(
        data: Dict[str, Any],
    ) -> Config:
        """Parse configuration dictionary into Config object."""
        # Validate required top-level keys
        if "version" not in data:
            raise ConfigurationError("Missing required field: version")
        if "input" not in data:
            raise ConfigurationError("Missing required field: input")
        if "output" not in data:
            raise ConfigurationError("Missing required field: output")
        if "mappings" not in data:
            raise ConfigurationError("Missing required field: mappings")

        # Parse schemas
        input_schema = InputSchema.from_dict(data["input"])
        output_schema = OutputSchema.from_dict(data["output"])

        # Parse mappings
        mappings = []
        for idx, mapping_data in enumerate(data["mappings"]):
            try:
                mapping = ConfigParser._parse_mapping(mapping_data)
                mappings.append(mapping)
            except Exception as e:
                raise ConfigurationError(f"Error in mapping #{idx + 1}: {e}")

        # Create config
        config = Config(
            version=data["version"],
            input_schema=input_schema,
            output_schema=output_schema,
            mappings=mappings,
        )

        # Validate config
        config.validate()

        return config

    @staticmethod
    def _parse_mapping(
        data: Dict[str, Any],
    ) -> MappingRule:
        """Parse a single mapping rule."""
        if "output" not in data:
            raise ConfigurationError("Mapping missing required field: output")

        # Parse type conversion if present
        type_conversion = None
        if "type_conversion" in data:
            type_conversion = TypeConversion.from_dict(data["type_conversion"])

        # Parse conditions if present
        conditions = []
        if "conditions" in data:
            for cond_data in data["conditions"]:
                conditions.append(Condition.from_dict(cond_data))

        return MappingRule(
            output=data["output"],
            source=data.get("source"),
            expression=data.get("expression"),
            value=data.get("value"),
            transform=data.get("transform"),
            default=data.get("default"),
            type_conversion=type_conversion,
            conditions=conditions,
        )
