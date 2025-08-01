# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
# This step is cached and only re-run if the lockfile or pyproject.toml changes
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Clean up the virtual environment to reduce image size
RUN find /app/.venv -name '__pycache__' -type d -exec rm -rf {} + && \
    find /app/.venv -name '*.pyc' -delete && \
    find /app/.venv -name '*.pyo' -delete && \
    find /app/.venv -name '*.pyd' -delete && \
    find /app/.venv -name 'test*' -type d -exec rm -rf {} + && \
    echo "Cleaned up .venv"

# --- Final Stage ---
# Use a slim image for a smaller final size
FROM python:3.13-slim-bookworm

# Install git for potential dependencies that might need it during runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create a non-root user for security
RUN groupadd -r app && useradd -r -g app -d /home/app -s /bin/bash -c "App user" app && \
    mkdir -p /home/app && \
    chown -R app:app /home/app

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy the application source code
COPY --from=builder --chown=app:app /app/src /app/src

# Place the virtual environment's executables at the front of the PATH
ENV PATH="/app/.venv/bin:$PATH"
# Set PYTHONPATH so that imports from /app work correctly
ENV PYTHONPATH=/app

# Switch to the non-root user
USER app

# Run the MCP server using its main entrypoint as a module
# This ensures the environment (e.g., from .env file if mounted) is set up correctly.
# The .env file itself should be provided at runtime, not baked into the image.
CMD ["python", "-m", "src.telegram_mcp.main"]
