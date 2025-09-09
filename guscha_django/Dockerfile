# Оптимизированный Dockerfile для Django приложения
# Многоступенчатая сборка для уменьшения размера образа

# Стадия сборки
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

# Продакшн стадия
FROM python:3.11.6-slim as production

# Метаданные для продакшн образа
LABEL stage="production"

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копирование виртуального окружения из стадии сборки
COPY --from=builder /opt/venv /opt/venv

# Создание пользователя app
RUN addgroup --system app && adduser --system --group app

# Установка рабочей директории
WORKDIR $APP_HOME

# Создание необходимых директорий
RUN mkdir -p $APP_HOME/static_root $APP_HOME/logs $APP_HOME/telegram_bot/logs $APP_HOME/media $APP_HOME/backups

# Копирование файлов приложения (порядок оптимизирован для кэширования)
COPY manage.py $APP_HOME/
COPY start_django_server.py $APP_HOME/
COPY guscha_project/ $APP_HOME/guscha_project/
COPY apps/ $APP_HOME/apps/
COPY telegram_bot/ $APP_HOME/telegram_bot/
COPY templates/ $APP_HOME/templates/
COPY static/ $APP_HOME/static/

# Копирование и настройка скрипта запуска
COPY scripts/start.sh $APP_HOME/start.sh
RUN chmod +x $APP_HOME/start.sh

# Устанавливаем права доступа для пользователя app
RUN chown -R app:app $APP_HOME

# Открытие порта
EXPOSE 8000

# Healthcheck для мониторинга состояния
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)" || exit 1

# Запуск приложения
CMD ["./start.sh"]