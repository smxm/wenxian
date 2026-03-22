class LiteratureScreeningError(Exception):
    """Base exception for the project."""


class ConfigValidationError(LiteratureScreeningError):
    """Raised when the run configuration is invalid."""


class BibtexParseError(LiteratureScreeningError):
    """Raised when BibTeX parsing fails."""


class DeduplicationError(LiteratureScreeningError):
    """Raised when deduplication fails."""


class ModelRequestError(LiteratureScreeningError):
    """Raised when the model request fails."""


class ResponseParseError(LiteratureScreeningError):
    """Raised when the model response cannot be parsed."""


class SchemaValidationError(LiteratureScreeningError):
    """Raised when structured data does not match schema."""


class ReportExportError(LiteratureScreeningError):
    """Raised when report export fails."""

