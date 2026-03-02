###############################################################################
# MULTI-STAGE DOCKERFILE: REACT FRONTEND BUILD + DJANGO BACKEND (Render)
###############################################################################

########################
# 1) FRONTEND BUILD   #
########################

FROM node:20-alpine AS frontend-build

WORKDIR /frontend

# Кэшируем установки зависимостей
COPY guscha_django_frontend/package*.json ./
RUN npm install

# Копируем исходники фронтенда и собираем
COPY guscha_django_frontend/ ./
ENV DISABLE_ESLINT_PLUGIN=true
RUN npm run build


########################
# 2) BACKEND + GUNICORN
########################

FROM python:3.11.6-slim AS production

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Copy backend requirements first (for caching)
COPY guscha_django/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy Django project
COPY guscha_django/ /app

# Copy built frontend into Django static_root
RUN mkdir -p static_root
COPY --from=frontend-build /frontend/build/ /app/static_root/

# Expose port (Render пробрасывает свой $PORT)
EXPOSE 8000

# Apply migrations, collectstatic (на всякий случай) и запустить Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && gunicorn --bind 0.0.0.0:$PORT --workers 3 guscha_project.wsgi:application"]
