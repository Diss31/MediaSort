# Same image devcontainer.json used directly before; the build step bakes in corporate
# proxy CAs (needed before any in-container HTTPS call) and the actionlint binary.
FROM mcr.microsoft.com/devcontainers/python:3.12

# Docker initializes an empty named volume from this directory's ownership.
# Keep the VS Code server and Copilot volumes writable by the non-root remote user.
RUN install -d -o vscode -g vscode \
    /home/vscode/.vscode-server \
    /home/vscode/.copilot /home/vscode/.copilot/session-state

# A TLS-intercepting proxy (e.g. Bluecoat) re-signs public hosts with its own CA, so
# without this trust the actionlint download below fails certificate verification.
# Certs come from gitignored .devcontainer/*.crt files (see README).
# devcontainer.json is listed alongside the wildcard because COPY fails the build when
# a wildcard alone matches nothing, i.e. on networks that need no extra CA.
COPY devcontainer.json *.crt /tmp/extra-ca/
RUN set -e; \
    rm /tmp/extra-ca/devcontainer.json; \
    if [ -n "$(ls -A /tmp/extra-ca)" ]; then \
        cp /tmp/extra-ca/*.crt /usr/local/share/ca-certificates/; \
        update-ca-certificates; \
    fi; \
    rm -rf /tmp/extra-ca

# actionlint checks the GitHub Actions workflows. ADD re-fetches this URL at every build
# and busts the layer below when its content changes; upstream bumps the version default
# in this script on each release, so a plain container rebuild picks up new releases
# without --no-cache. Installed at build time (as root) into /usr/local/bin, the standard
# PATH location, rather than from postCreateCommand which runs as the non-root user.
ADD https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash /tmp/download-actionlint.bash
RUN bash /tmp/download-actionlint.bash latest /usr/local/bin \
    && rm /tmp/download-actionlint.bash
