#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from apps.accounts.models import User

# Проверяем существующих суперпользователей
superusers = User.objects.filter(is_superuser=True)
print(f"Найдено суперпользователей: {superusers.count()}")

for user in superusers:
    print(f"ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Username: {getattr(user, 'username', 'N/A')}")
    print(f"Phone: {getattr(user, 'phone', 'N/A')}")
    print(f"Active: {user.is_active}")
    print(f"Staff: {user.is_staff}")
    print(f"Superuser: {user.is_superuser}")
    print("-" * 30)

# Создаем нового суперпользователя если нужно
if not User.objects.filter(email='admin@guscha.com', is_superuser=True).exists():
    print("Создаем нового суперпользователя...")
    user = User.objects.create_superuser(
        email='admin@guscha.com',
        password='admin123',
        phone='+79999999999'
    )
    print(f"Создан суперпользователь: {user.email}")
else:
    print("Суперпользователь admin@guscha.com уже существует")