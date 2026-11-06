# https://docs.astral.sh/uv/guides/integration/docker/
# Alternative: https://github.com/astral-sh/uv/issues/7758#issuecomment-3263282018
FROM ghcr.io/astral-sh/uv:alpine

# Allow uv to install dependencies from git sources
RUN apk add --no-cache --virtual .git git

# # pyinstrument/pyyaml have no musl wheels for CPython 3.15 and build from
# # source — alpine's uv image ships no compiler by default
# RUN apk add --no-cache build-base

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON=3.14
ENV UV_PYTHON_CACHE_DIR=/root/.cache/uv/python

RUN --mount=type=cache,target=/root/.cache/uv \
    uv python install

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project

# --locked ensures uv.lock is in sync with pyproject.toml.
# Subsequent commands can skip checking it with --frozen.
ENV UV_FROZEN=1

COPY alembic.ini pyproject.toml README.md uv.lock ./
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Now the venv is synced, tell uv to not sync again during `uv run`.
ENV UV_NO_SYNC=1

# Clean up unnecessary build dependencies
RUN apk del .git

ENV PATH=/app/.venv/bin:${PATH}
ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT
ENTRYPOINT ["uv", "run"]
CMD ["quickticket", "run"]
