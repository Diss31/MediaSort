# Shared base image: dependencies only, deliberately no project code.
#
# Strategy ii-b. Because the source is not copied here, editing a filter leaves
# this image a cache hit and only rebuilds that filter's thin layer, instead of
# invalidating the base and forcing every filter image to rebuild and re-push.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Only the dependency manifests, so this layer's cache key is the dependency
# set rather than the source tree.
COPY pyproject.toml uv.lock README.md ./

# --no-install-project installs the resolved dependencies without building
# mediasort itself, which is exactly what plain `pip install .` cannot express.
# --locked fails loudly if uv.lock has drifted from pyproject.toml.
RUN uv sync --locked --no-install-project --no-editable
