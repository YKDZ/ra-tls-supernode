"""Helpers for calling the simulated DCAP verification library."""

from __future__ import annotations

import ctypes
import logging
import os
import time
from dataclasses import dataclass

from .exceptions import QuoteVerificationError

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class QuoteVerificationOutcome:
    """Result tuple returned by the simulated DCAP verifier."""

    status: int
    collateral_expiration_status: int
    result_code: int


class QuoteVerifier:
    """Thin ctypes wrapper around the simulated DCAP verification library."""

    def __init__(self, library_path: str | None = None) -> None:
        self._library_path = library_path or os.environ.get(
            "DCAP_LIBRARY_PATH", "libdcap_quoteverify_stub.so"
        )
        self._lib = self._load_library(self._library_path)
        self._configure_signatures()

    @staticmethod
    def _load_library(path: str) -> ctypes.CDLL:
        candidate_paths = (path, os.path.join(os.getcwd(), path))
        last_error: Exception | None = None
        for candidate in candidate_paths:
            try:
                return ctypes.cdll.LoadLibrary(candidate)
            except OSError as exc:  # pragma: no cover - defensive logging
                last_error = exc
        raise QuoteVerificationError(
            f"unable to load DCAP verification library from '{path}': {last_error}"
        )

    def _configure_signatures(self) -> None:
        self._lib.sgx_qv_verify_quote.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_longlong,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        self._lib.sgx_qv_verify_quote.restype = ctypes.c_uint32

        self._lib.sgx_qv_get_quote_supplemental_data_size.argtypes = [
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self._lib.sgx_qv_get_quote_supplemental_data_size.restype = ctypes.c_uint32

    def verify_quote(self, quote: bytes) -> QuoteVerificationOutcome:
        if not quote:
            raise QuoteVerificationError("empty quote provided for verification")

        quote_buffer = (ctypes.c_uint8 * len(quote)).from_buffer_copy(quote)
        supp_size = ctypes.c_uint32(0)
        supp_result = self._lib.sgx_qv_get_quote_supplemental_data_size(
            ctypes.byref(supp_size)
        )

        supplemental_buffer = None
        supplemental_length = ctypes.c_uint32(0)

        if supp_result == 0 and supp_size.value > 0:
            supplemental_buffer = (ctypes.c_uint8 * supp_size.value)()
            supplemental_length = ctypes.c_uint32(supp_size.value)

        expiration_status = ctypes.c_uint32(1)
        quote_result = ctypes.c_uint32(0)

        status = self._lib.sgx_qv_verify_quote(
            quote_buffer,
            ctypes.c_uint32(len(quote)),
            ctypes.c_void_p(0),
            ctypes.c_longlong(int(time.time())),
            ctypes.byref(expiration_status),
            ctypes.byref(quote_result),
            ctypes.c_void_p(0),
            supplemental_length,
            supplemental_buffer,
        )

        outcome = QuoteVerificationOutcome(
            status=status,
            collateral_expiration_status=expiration_status.value,
            result_code=quote_result.value,
        )

        if status != 0 or outcome.collateral_expiration_status != 0 or outcome.result_code != 0:
            raise QuoteVerificationError(
                "DCAP verification failed: status=%s collateral=%s result=%s"
                % (status, outcome.collateral_expiration_status, outcome.result_code)
            )

        _LOGGER.debug("DCAP verification succeeded: %s", outcome)
        return outcome
