FROM flwr/supernode:1.22.0 AS base
ENV PATH="/root/.local/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

USER root
RUN apk add --no-cache build-base python3 py3-pip bash curl ca-certificates \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -sf /root/.local/bin/uv /usr/local/bin/uv

FROM base AS deps
WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode --no-install-project

FROM base AS runner
ENV PATH="/app/.venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/app/csrc

COPY --from=deps /app .
COPY src /app/src
COPY csrc/libdcap_quoteverify_stub.a /app/csrc/
COPY csrc/libdcap_quoteverify_stub.so /app/csrc/

RUN python -m compileall src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
