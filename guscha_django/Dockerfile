# Dockerfile для Django приложения с предварительно собранным фронтендом
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Обновляем pip и устанавливаем основные инструменты
RUN pip install --upgrade pip

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости (кэшируется)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только необходимые файлы для быстрой пересборки
COPY manage.py .
COPY guscha_project/ ./guscha_project/
COPY apps/ ./apps/
COPY telegram_bot/ ./telegram_bot/
COPY templates/ ./templates/
COPY static/ ./static/
COPY start_django_server.py .

# Убеждаемся, что static_root и logs существуют
RUN mkdir -p /app/static_root /app/logs /app/telegram_bot/logs

# Копируем скрипт запуска
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Открываем порт
EXPOSE 8000

# Запускаем через скрипт
CMD ["/app/start.sh"]