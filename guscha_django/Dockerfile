# ============================================================================
# SIMPLE DOCKERFILE FOR DJANGO DEVELOPMENT
# ============================================================================

FROM python:3.11.6-slim as production

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p logs static_root media

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "guscha_project.wsgi:application"]
