"""Custom exceptions for FileMapper."""


class FileMapperError(Exception):
    """Base exception for all FileMapper errors."""

    pass


class ConfigurationError(FileMapperError):
    """Raised when configuration is invalid or cannot be parsed."""

    pass


class ValidationError(FileMapperError):
    """Raised when data validation fails."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class MappingError(FileMapperError):
    """Raised when mapping execution fails."""

    pass


class TransformationError(FileMapperError):
    """Raised when a transformation operation fails."""

    pass


class ExpressionError(FileMapperError):
    """Raised when expression evaluation fails."""

    pass
