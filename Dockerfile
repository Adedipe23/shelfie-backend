# Dockerfile for ISMS FastAPI Application
# Optimized for production deployment with Dokploy

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV_MODE=production \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r isms && useradd -r -g isms isms

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=isms:isms . .

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R isms:isms logs && chmod 755 logs

# Switch to non-root user
USER isms

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - use manage.py runprod for production with gunicorn
CMD ["python", "manage.py", "runprod", "--host", "0.0.0.0", "--port", "8000"]
