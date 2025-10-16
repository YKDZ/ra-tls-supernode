"""CLI for starting the RA-TLS proxy."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from .proxy import ProxyConfig, RaTLSProxy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RA-TLS transparent proxy")
    parser.add_argument("superlink", help="Target superlink in host:port format")
    parser.add_argument(
        "--listen-host",
        default=os.environ.get("RA_TLS_LISTEN_HOST", "0.0.0.0"),
        help="Listening interface",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=int(os.environ.get("RA_TLS_LISTEN_PORT", "8443")),
        help="Listening port",
    )
    parser.add_argument(
        "--connect-timeout",
        type=float,
        default=float(os.environ.get("RA_TLS_CONNECT_TIMEOUT", "10")),
        help="Upstream connect timeout seconds",
    )
    parser.add_argument(
        "--handshake-timeout",
        type=float,
        default=float(os.environ.get("RA_TLS_HANDSHAKE_TIMEOUT", "30")),
        help="TLS handshake timeout seconds",
    )
    parser.add_argument(
        "--upstream-connect-host",
        default=os.environ.get("RA_TLS_UPSTREAM_CONNECT_HOST"),
        help="Concrete host/IP used for establishing upstream TCP sockets",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("RA_TLS_LOG_LEVEL", "INFO"),
        help="Logging level",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    host, _, port = args.superlink.partition(":")
    if not host or not port:
        raise SystemExit("superlink must be in host:port format")

    config = ProxyConfig(
        listen_host=args.listen_host,
        listen_port=args.listen_port,
        upstream_host=host,
        upstream_port=int(port),
        upstream_connect_host=args.upstream_connect_host,
        connect_timeout=args.connect_timeout,
        handshake_timeout=args.handshake_timeout,
    )

    proxy = RaTLSProxy(config)
    try:
        asyncio.run(proxy.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
