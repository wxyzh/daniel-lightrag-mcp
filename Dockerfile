FROM python:3.11-slim

WORKDIR /app

# Copy application code first (required for editable install)
COPY src/ ./src/
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Environment variables with defaults
ENV LIGHTRAG_BASE_URL=http://localhost:9621
ENV LIGHTRAG_TIMEOUT=30
ENV LIGHTRAG_TOOL_PREFIX=
ENV LOG_LEVEL=INFO

# Default: HTTP mode on port 8080
# For stdio mode (Claude Desktop), use:
#   docker run --rm -i lightrag-mcp python -m daniel_lightrag_mcp
CMD ["daniel-lightrag-http", "--host", "0.0.0.0", "--port", "8080"]
