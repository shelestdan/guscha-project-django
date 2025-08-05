#!/bin/bash

# Собираем статические файлы Django с доступными переменными окружения
python manage.py collectstatic --noinput

# Запускаем сервер
python start_with_ngrok.py