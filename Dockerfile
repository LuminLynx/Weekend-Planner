# Multi-stage build for smaller image
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir --user -e .

FROM python:3.11-slim
WORKDIR /app
# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local
COPY app ./app
COPY pyproject.toml ./

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
ENTRYPOINT ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
