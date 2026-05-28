class KmsError(Exception):
    """Base error for user-facing KMS CLI failures."""


class ConfigError(KmsError):
    """Raised when local CLI configuration is missing or invalid."""


class AuthError(KmsError):
    """Raised when authentication is missing, expired, or rejected."""


class HttpRequestError(KmsError):
    """Raised when an HTTP request fails before receiving a response."""


class HttpStatusError(KmsError):
    """Raised when the service returns a non-success response."""


class InvalidJsonError(KmsError):
    """Raised when the service returns a body that is not valid JSON."""
