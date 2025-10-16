#!/usr/bin/env bash
set -euo pipefail

: "${SUPERLINK_HOST:?SUPERLINK_HOST not set}"
: "${SUPERLINK_PORT:?SUPERLINK_PORT not set}"

LISTEN_HOST="${RA_TLS_LISTEN_HOST:-127.0.0.1}"
LISTEN_PORT="${RA_TLS_LISTEN_PORT:-${SUPERLINK_PORT}}"

if [[ -z "${LISTEN_PORT}" ]]; then
  echo "RA_TLS_LISTEN_PORT must not be empty" >&2
  exit 1
fi

UPSTREAM_CONNECT_HOST="${RA_TLS_UPSTREAM_CONNECT_HOST:-}"
if [[ -z "${UPSTREAM_CONNECT_HOST}" ]]; then
  if ! command -v ra-tls-resolve-host >/dev/null 2>&1; then
    echo "ra-tls-resolve-host command not found" >&2
    exit 1
  fi
  if ! UPSTREAM_CONNECT_HOST="$(ra-tls-resolve-host "${SUPERLINK_HOST}")"; then
    echo "Unable to resolve ${SUPERLINK_HOST}" >&2
    exit 1
  fi
fi

if [[ -z "${UPSTREAM_CONNECT_HOST}" ]]; then
  echo "Unable to determine upstream connect host" >&2
  exit 1
fi

if ! grep -qE "^[^#]*\b${SUPERLINK_HOST}\b" /etc/hosts; then
  echo "${LISTEN_HOST} ${SUPERLINK_HOST}" >> /etc/hosts
fi

proxy_args=(
  --listen-host "${LISTEN_HOST}"
  --listen-port "${LISTEN_PORT}"
  --connect-timeout "${RA_TLS_CONNECT_TIMEOUT:-10}"
  --handshake-timeout "${RA_TLS_HANDSHAKE_TIMEOUT:-30}"
  --upstream-connect-host "${UPSTREAM_CONNECT_HOST}"
  "${SUPERLINK_HOST}:${SUPERLINK_PORT}"
)

if [[ -n "${RA_TLS_LOG_LEVEL:-}" ]]; then
  proxy_args+=(--log-level "${RA_TLS_LOG_LEVEL}")
fi

ra-tls-proxy "${proxy_args[@]}" &
proxy_pid=$!

cleanup() {
  if kill -0 "${proxy_pid}" 2>/dev/null; then
    kill "${proxy_pid}" 2>/dev/null || true
    wait "${proxy_pid}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

sleep 0.2

exec flower-supernode "$@"

