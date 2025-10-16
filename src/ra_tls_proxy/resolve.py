"""Utility helpers for resolving superlink host names."""

from __future__ import annotations

import argparse
import socket
import sys


def resolve_host(host: str) -> str:
    """Return the preferred address for *host*, favouring IPv4 when available."""

    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:  # pragma: no cover - resolution depends on runtime
        raise ValueError(f"unable to resolve {host!r}: {exc}") from exc

    if not infos:
        raise ValueError(f"no addresses resolved for {host!r}")

    for family, _, _, _, sockaddr in infos:
        if family == socket.AF_INET:
            return sockaddr[0]

    return infos[0][4][0]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="resolve host to connection address")
    parser.add_argument("host", help="Host name to resolve")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        address = resolve_host(args.host)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(address)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    sys.exit(main())
