# Toolbox MCP Server — fat container with all runtime dependencies
#
# Includes: ssh, curl, ffmpeg, inkscape, gh CLI, docker CLI, yt-dlp
# Python deps: fastmcp, openai, jsonschema, pyyaml, etc.
#
# Build:  docker build -t ghcr.io/matthewdart/toolbox:latest .
# Run:    docker compose up -d

FROM python:3.11-slim AS base

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    ffmpeg \
    inkscape \
    git \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# gh CLI (GitHub)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI only (no daemon — talks to host socket)
RUN ARCH=$(uname -m) && \
    curl -fsSL "https://download.docker.com/linux/static/stable/${ARCH}/docker-27.5.1.tgz" \
      | tar xz --strip-components=1 -C /usr/local/bin docker/docker

# Docker Compose V2 plugin
RUN ARCH=$(uname -m) && \
    mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -fsSL "https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-${ARCH}" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# --- Non-root user ---
RUN groupadd -g 1001 toolbox && useradd -u 1001 -g toolbox -m toolbox

WORKDIR /app

# --- Python dependencies ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application source ---
COPY core/ core/
COPY capabilities/ capabilities/
COPY adapters/ adapters/
COPY compose/ compose/

# Ensure the package is importable
ENV PYTHONPATH=/app

# --- Runtime config ---
# stdio by default (gateway uses docker exec -i)
# Set TOOLBOX_TRANSPORT=http for standalone HTTP mode
ENV TOOLBOX_TRANSPORT=stdio
ENV TOOLBOX_HOST=127.0.0.1
ENV TOOLBOX_PORT=8768

USER toolbox

# SSH config mount point (docker-compose mounts ~/.ssh here)
RUN mkdir -p /home/toolbox/.ssh && chmod 700 /home/toolbox/.ssh

ENTRYPOINT ["python", "-m", "adapters.mcp.server"]
