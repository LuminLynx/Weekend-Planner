# Multi-stage build for minimal image size (<200MB target)
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --user -e .

# Final stage - minimal runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy only Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app ./app
COPY pyproject.toml ./

# Ensure data directory exists
RUN mkdir -p data

# Make scripts in .local usable
ENV PATH=/root/.local/bin:$PATH

# Clean up unnecessary files to reduce image size
RUN find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -name "*.so" -exec strip --strip-unneeded {} \; 2>/dev/null || true

EXPOSE 8000

# Use uvicorn for the server
ENTRYPOINT ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
