#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from django.db import connection

def check_background_content_tables():
    """Проверка существования таблиц background_content"""
    cursor = connection.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    print("Все таблицы в базе данных:")
    for table in sorted(all_tables):
        print(f"  - {table}")
    
    print("\nТаблицы background_content:")
    bg_tables = [table for table in all_tables if 'background_content' in table]
    if bg_tables:
        for table in bg_tables:
            print(f"  - {table}")
    else:
        print("  Таблицы background_content не найдены!")
    
    # Проверяем статус миграций
    cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app = 'background_content';")
    migrations = cursor.fetchall()
    
    print("\nСтатус миграций background_content:")
    if migrations:
        for app, name, applied in migrations:
            status = "✓ Применена" if applied else "✗ Не применена"
            print(f"  - {name}: {status}")
    else:
        print("  Миграции background_content не найдены!")

if __name__ == '__main__':
    check_background_content_tables()