# https://docs.astral.sh/uv/guides/integration/docker/
# Alternative: https://github.com/astral-sh/uv/issues/7758#issuecomment-3263282018
FROM ghcr.io/astral-sh/uv:alpine

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_LOCKED=1
ENV UV_NO_DEV=1
ENV UV_PYTHON=3.14

WORKDIR /app
COPY --link pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project
# COPY --link LICENSE README.md ./
COPY --link README.md ./
COPY --link src/ src/
RUN --mount=type=cache,target=/root/.cache/uv uv sync

ENV PATH=/app/.venv/bin:${PATH}
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT
ENTRYPOINT ["quickticket"]
