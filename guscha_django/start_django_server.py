#!/usr/bin/env python
"""
Скрипт для запуска Django-сервера.
"""
import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')

# Инициализируем Django
django.setup()

if __name__ == '__main__':
    print('Запуск Django-сервера на http://0.0.0.0:8000')
    print('Для остановки сервера нажмите Ctrl+C')
    
    # Собираем статические файлы
    print('Сбор статических файлов...')
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Запускаем сервер на порту 8000
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])