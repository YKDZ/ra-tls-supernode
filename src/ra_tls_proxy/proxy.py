"""Implementation of the RA-TLS enforcing transparent proxy."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import ssl
import time
from dataclasses import dataclass

from .dcap import QuoteVerifier
from .exceptions import HandshakeTimeoutError, QuoteMissingError, QuoteVerificationError
from .tls import extract_sgx_quote_from_cert

_LOGGER = logging.getLogger(__name__)

DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_HANDSHAKE_TIMEOUT = 30


@dataclass(slots=True)
class ProxyConfig:
    """Runtime configuration for the proxy."""

    listen_host: str = "0.0.0.0"
    listen_port: int = 8443
    upstream_host: str = "127.0.0.1"
    upstream_port: int = 443
    upstream_connect_host: str | None = None
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT
    handshake_timeout: float = DEFAULT_HANDSHAKE_TIMEOUT
    buffer_size: int = 64 * 1024

    def upstream_target(self) -> str:
        """Return the concrete host used for TCP connections."""

        return self.upstream_connect_host or self.upstream_host


class RaTLSProxy:
    """Asyncio-based bidirectional TCP proxy with RA-TLS gating."""

    def __init__(
        self,
        config: ProxyConfig,
        quote_verifier: QuoteVerifier | None = None,
    ) -> None:
        self._config = config
        self._quote_verifier = quote_verifier or QuoteVerifier()

    async def run(self) -> None:
        """Start serving until cancelled."""

        server = await asyncio.start_server(
            self._handle_client,
            host=self._config.listen_host,
            port=self._config.listen_port,
            reuse_port=True,
        )
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        _LOGGER.info("Proxy listening on %s", addresses)

        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peername = writer.get_extra_info("peername")
        start_time = time.time()
        _LOGGER.info("Incoming connection from %s", peername)

        upstream_reader: asyncio.StreamReader | None = None
        upstream_writer: asyncio.StreamWriter | None = None
        try:
            quote = await self._fetch_quote()
            if quote is None:
                _LOGGER.info(
                    "Upstream %s:%d is not serving TLS; forwarding without attestation",
                    self._config.upstream_host,
                    self._config.upstream_port,
                )
            else:
                self._quote_verifier.verify_quote(quote)
            upstream_reader, upstream_writer = await self._open_upstream()
            await self._pump(reader, writer, upstream_reader, upstream_writer)
        except (QuoteVerificationError, QuoteMissingError, HandshakeTimeoutError) as exc:
            _LOGGER.warning("Connection from %s rejected: %s", peername, exc)
        except Exception as exc:  # pragma: no cover - defensive logging
            _LOGGER.exception("Unexpected proxy error: %s", exc)
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            if upstream_writer is not None:
                upstream_writer.close()
                with contextlib.suppress(Exception):
                    await upstream_writer.wait_closed()
            _LOGGER.info(
                "Connection from %s closed after %.2fs",
                peername,
                time.time() - start_time,
            )

    async def _fetch_quote(self) -> bytes | None:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connect_host = self._config.upstream_target()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    connect_host,
                    self._config.upstream_port,
                    ssl=context,
                    server_hostname=self._config.upstream_host,
                    ssl_handshake_timeout=self._config.handshake_timeout,
                ),
                timeout=self._config.connect_timeout + self._config.handshake_timeout,
            )
        except asyncio.TimeoutError as exc:
            raise HandshakeTimeoutError("TLS handshake timeout") from exc
        except ssl.SSLError as exc:
            if self._is_non_tls_error(exc):
                _LOGGER.debug(
                    "Detected non-TLS upstream during handshake: %s", exc
                )
                return None
            raise QuoteMissingError("failed to obtain upstream certificate") from exc
        except Exception as exc:  # pragma: no cover - upstream connection errors
            raise QuoteMissingError("failed to obtain upstream certificate") from exc

        try:
            ssl_object = writer.get_extra_info("ssl_object")
            if ssl_object is None:
                raise QuoteMissingError("TLS object missing")

            cert_chain = ssl_object.getpeercert(binary_form=True)
            if not cert_chain:
                raise QuoteMissingError("upstream certificate missing")

            return extract_sgx_quote_from_cert(cert_chain)
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    @staticmethod
    def _is_non_tls_error(error: ssl.SSLError) -> bool:
        reason = getattr(error, "reason", "")
        reason_text = reason.upper() if isinstance(reason, str) else ""
        message_text = " ".join(str(arg) for arg in error.args).upper()
        markers = ("WRONG_VERSION_NUMBER", "UNKNOWN_PROTOCOL")
        return any(marker in reason_text or marker in message_text for marker in markers)

    async def _open_upstream(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        try:
            return await asyncio.wait_for(
                asyncio.open_connection(
                    self._config.upstream_target(),
                    self._config.upstream_port,
                ),
                timeout=self._config.connect_timeout,
            )
        except asyncio.TimeoutError as exc:
            raise HandshakeTimeoutError("upstream connection timeout") from exc

    async def _pump(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
        upstream_reader: asyncio.StreamReader,
        upstream_writer: asyncio.StreamWriter,
    ) -> None:
        """Relay bytes between client and upstream after verification."""

        async def relay(
            source: asyncio.StreamReader, target: asyncio.StreamWriter, direction: str
        ) -> None:
            try:
                while True:
                    data = await source.read(self._config.buffer_size)
                    if not data:
                        break
                    target.write(data)
                    await target.drain()
            except Exception as exc:  # pragma: no cover - defensive logging
                _LOGGER.debug("%s relay stopped: %s", direction, exc)
            finally:
                target.close()

        await asyncio.gather(
            relay(client_reader, upstream_writer, "client->upstream"),
            relay(upstream_reader, client_writer, "upstream->client"),
            return_exceptions=True,
        )
