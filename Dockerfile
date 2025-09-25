FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and ensure stdout/stderr are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir "poetry==1.8.3"

# Copy dependency manifests first for better build caching
COPY pyproject.toml poetry.lock ./

# Install runtime dependencies only (no dev)
RUN poetry config virtualenvs.create false \
 && poetry lock --no-update \
 && poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY app ./app

EXPOSE 8000

# Default environment variables (override as needed)
ENV PORT=8000

# Start the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


