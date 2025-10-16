"""TLS parsing helpers for extracting SGX quotes from certificates."""

from __future__ import annotations

import logging

from cryptography import x509

from .exceptions import QuoteMissingError

_LOGGER = logging.getLogger(__name__)


EXTENSION_OID_QUOTE = x509.ObjectIdentifier("1.2.840.113741.1.13.1")


def extract_sgx_quote_from_cert(cert_bytes: bytes) -> bytes:
    """Extract the opaque SGX quote from a certificate extension."""

    try:
        cert = x509.load_der_x509_certificate(cert_bytes)
    except ValueError as exc:  # pragma: no cover - certificate parsing error
        raise QuoteMissingError("unable to parse upstream certificate") from exc

    try:
        extension = cert.extensions.get_extension_for_oid(EXTENSION_OID_QUOTE)
    except x509.ExtensionNotFound as exc:
        raise QuoteMissingError("SGX quote extension missing") from exc

    value = extension.value
    if hasattr(value, "value"):
        raw = value.value
    else:  # pragma: no cover - defensive for custom extensions
        raw = bytes(value)

    if not raw:
        raise QuoteMissingError("SGX quote extension empty")

    _LOGGER.debug("Extracted SGX quote of length %d", len(raw))
    return raw
