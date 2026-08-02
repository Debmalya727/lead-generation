FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install minimal system utilities required for builds and container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependency requirements first for Docker layer caching
COPY requirements.txt .

# Install Python application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright chromium browser binaries alongside official OS dependencies automatically
RUN python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root security user and prepare storage volumes
RUN useradd -m -u 1000 appuser && \
    mkdir -p /ms-playwright /app/uploads /app/reports /app/exports /app/screenshots /app/logs && \
    chown -R appuser:appuser /ms-playwright /app

# Copy application source code and assign ownership to appuser
COPY . .
RUN chown -R appuser:appuser /app

# Switch to restricted non-root execution user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
