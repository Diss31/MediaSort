# Scheduler image: thin layer on top of the shared dependency base.
ARG BASE_IMAGE=mediasort-base:latest
FROM ${BASE_IMAGE}

# Scheduler-only extra dependencies (the YAML parser), installed before the
# source is copied so this layer stays cached across code edits. pyproject.toml
# and uv.lock come from the base image.
RUN uv sync --locked --extra scheduler --no-install-project --no-editable

COPY src/ ./src/

# Every dependency is already present, so this only installs mediasort itself.
RUN uv sync --locked --extra scheduler --no-editable

ENTRYPOINT ["mediasort-scheduler"]
