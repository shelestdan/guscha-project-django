# ============================================================================
# OPTIMIZED DOCKERFILE FOR DJANGO APPLICATION
# Multi-stage build for minimal image size
# ============================================================================

# Build stage
FROM python:3.11.6-slim as builder

# Метаданные образа
LABEL maintainer="guscha@example.com" \
      version="1.0" \
      description="Django application with optimized Docker build" \
      org.opencontainers.image.source="https://github.com/guscha/django-app"

# Переменные окружения для оптимизации Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей в одном слое
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Обновление pip
RUN pip install --upgrade pip

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей (кэшируется при неизменном requirements.txt)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Production stage
FROM python:3.11.6-slim as production

# Production metadata
LABEL stage="production"

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-privileged user
RUN addgroup --system app && adduser --system --group app

# Set working directory
WORKDIR $APP_HOME

# Create necessary directories
RUN mkdir -p $APP_HOME/static_root $APP_HOME/logs $APP_HOME/telegram_bot/logs $APP_HOME/media $APP_HOME/backups $APP_HOME/profiles

# Copy application files (order optimized for caching)
COPY --chown=app:app manage.py $APP_HOME/
COPY --chown=app:app start_django_server.py $APP_HOME/
COPY --chown=app:app guscha_project/ $APP_HOME/guscha_project/
COPY --chown=app:app apps/ $APP_HOME/apps/
COPY --chown=app:app telegram_bot/ $APP_HOME/telegram_bot/
COPY --chown=app:app templates/ $APP_HOME/templates/
COPY --chown=app:app static/ $APP_HOME/static/

# Copy and setup startup script
COPY --chown=app:app scripts/start.sh $APP_HOME/start.sh
RUN chmod +x $APP_HOME/start.sh

# Switch to non-privileged user
USER app

# Expose port
EXPOSE 8000

# Health check for monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Start application
CMD ["./start.sh"]