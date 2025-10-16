"""Domain-specific exceptions for the RA-TLS proxy."""

class ProxyError(Exception):
    """Base exception for proxy errors."""


class QuoteMissingError(ProxyError):
    """Raised when an SGX quote cannot be located in the server certificate."""


class QuoteVerificationError(ProxyError):
    """Raised when the DCAP verification library reports an error."""


class HandshakeTimeoutError(ProxyError):
    """Raised when the TLS handshake does not complete in time."""
