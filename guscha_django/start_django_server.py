#!/usr/bin/env python
"""
Скрипт для запуска Django-сервера в production режиме с использованием waitress WSGI сервера.
"""
import os
import sys
from waitress import serve

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')

# Импортируем WSGI-приложение
from guscha_project.wsgi import application

if __name__ == '__main__':
    print('Запуск Django-сервера на http://127.0.0.1:8000')
    print('Для остановки сервера нажмите Ctrl+C')
    
    # Запускаем сервер на порту 8000
    serve(application, host='127.0.0.1', port=8000)