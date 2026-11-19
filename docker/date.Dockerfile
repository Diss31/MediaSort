# Date filter image: thin layer on top of the shared dependency base.
ARG BASE_IMAGE=mediasort-base:latest
FROM ${BASE_IMAGE}

COPY src/ ./src/

# Dependencies are already present from the base layer, so this installs the
# project itself plus the (currently empty) date-only extra.
RUN uv sync --locked --extra date --no-editable

ENTRYPOINT ["mediasort-date"]
