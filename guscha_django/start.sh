#!/bin/bash

# Скрипт запуска Django приложения
set -e

echo "Starting Django application..."

# Очистка и создание директории статических файлов (от root)
echo "Preparing static files directory..."
rm -rf /app/static_root/*
mkdir -p /app/static_root
chown -R app:app /app/static_root
chmod -R 755 /app/static_root
chown -R app:app /app

# Переключение на пользователя app для выполнения Django команд
echo "Switching to app user..."
exec su app -c '
set -e
cd /app

# Ожидание готовности базы данных
echo "Waiting for database to be ready..."
python manage.py migrate --noinput

# Сбор статических файлов
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Создание суперпользователя если не существует
echo "Creating superuser if not exists..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email=\"admin@example.com\").exists() or User.objects.create_superuser(\"admin@example.com\", \"admin123\")"

# Запуск Django сервера
echo "Starting Django development server..."
python start_django_server.py
'