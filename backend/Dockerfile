# Build stage / Production Dockerfile for UPSKILL AI FastAPI Backend
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    ENVIRONMENT=production

# Install essential system dependencies (libmagic, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a dedicated non-root user and group
RUN addgroup --system appgroup && adduser --system --group appuser

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code, database migrations, and configs
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Adjust permissions for non-root user
RUN chown -R appuser:appgroup /app

USER appuser

# Expose container port
EXPOSE 8000

# Health check against the /api/v1/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Launch uvicorn dynamically bound to $PORT (required by Render/Railway/Fly.io)
# Runs alembic migrations first if running against PostgreSQL in production
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
