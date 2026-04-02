# GCM MCP Relay - Dockerfile
# Multi-stage build for optimized production image

# ============================================================
# Stage 1: Builder - Install Python dependencies
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# Stage 2: Runtime - Minimal production image
# ============================================================
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r relay && useradd -r -g relay -u 1000 relay

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/relay/.local

# Copy application code (copy gcm_relay package directly to /app)
COPY --chown=relay:relay src/gcm_relay ./gcm_relay

# Copy scripts
COPY --chown=relay:relay scripts/entrypoint.sh /entrypoint.sh
COPY --chown=relay:relay scripts/config-loader.py /config-loader.py

# Make scripts executable
RUN chmod +x /entrypoint.sh /config-loader.py

# Create directories for config and logs
RUN mkdir -p /config /logs && chown relay:relay /logs

# Set environment variables
ENV PATH=/home/relay/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Switch to non-root user
USER relay

# Health check (for HTTP mode in Phase 2)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Use entrypoint script for configuration loading and validation
ENTRYPOINT ["/entrypoint.sh"]

# Default to stdio transport mode
CMD ["stdio"]