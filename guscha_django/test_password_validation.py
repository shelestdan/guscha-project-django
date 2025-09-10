#!/usr/bin/env python
"""
Скрипт для тестирования валидации паролей
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_django.settings')
django.setup()

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.accounts.repositories.auth_repository import AuthRepository
from apps.accounts.repositories.user_repository import UserRepository

def test_password_validation():
    """Тестирование валидации паролей"""
    print("=== Тестирование валидации паролей ===")
    
    # Тестовые пароли
    weak_passwords = ['123', '12345', 'password', 'qwerty', 'abc']
    strong_passwords = ['MyStr0ngP@ssw0rd!', 'C0mpl3x_P@ssw0rd123', 'S3cur3_P@ss2024!']
    
    print("\n1. Тестирование Django validate_password:")
    
    # Тест слабых паролей
    for password in weak_passwords:
        try:
            validate_password(password)
            print(f"❌ ОШИБКА: Слабый пароль '{password}' прошел валидацию!")
        except ValidationError as e:
            print(f"✅ Слабый пароль '{password}' отклонен: {e}")
    
    # Тест сильных паролей
    for password in strong_passwords:
        try:
            validate_password(password)
            print(f"✅ Сильный пароль '{password}' принят")
        except ValidationError as e:
            print(f"❌ ОШИБКА: Сильный пароль '{password}' отклонен: {e}")
    
    print("\n2. Тестирование через UserRepository:")
    
    user_repo = UserRepository()
    
    # Создаем тестового пользователя
    try:
        test_user = User.objects.create_user(
            email='test_password@example.com',
            password='TempP@ssw0rd123!',
            first_name='Test',
            last_name='User'
        )
        print(f"✅ Тестовый пользователь создан: {test_user.email}")
        
        # Тестируем установку слабого пароля
        for password in weak_passwords:
            try:
                user_repo.set_password(test_user, password)
                print(f"❌ ОШИБКА: Слабый пароль '{password}' установлен через UserRepository!")
            except ValidationError as e:
                print(f"✅ Слабый пароль '{password}' отклонен UserRepository: {e}")
        
        # Тестируем установку сильного пароля
        try:
            user_repo.set_password(test_user, 'N3wStr0ng_P@ssw0rd!')
            print("✅ Сильный пароль успешно установлен через UserRepository")
        except ValidationError as e:
            print(f"❌ ОШИБКА: Сильный пароль отклонен UserRepository: {e}")
        
        # Удаляем тестового пользователя
        test_user.delete()
        print("✅ Тестовый пользователь удален")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестового пользователя: {e}")
    
    print("\n3. Тестирование через AuthRepository:")
    
    auth_repo = AuthRepository()
    
    # Создаем тестового пользователя
    try:
        test_user = User.objects.create_user(
            email='test_auth@example.com',
            password='TempP@ssw0rd123!',
            first_name='Test',
            last_name='Auth'
        )
        print(f"✅ Тестовый пользователь создан: {test_user.email}")
        
        # Тестируем установку слабого пароля
        for password in weak_passwords:
            try:
                auth_repo.set_password(test_user, password)
                print(f"❌ ОШИБКА: Слабый пароль '{password}' установлен через AuthRepository!")
            except ValidationError as e:
                print(f"✅ Слабый пароль '{password}' отклонен AuthRepository: {e}")
        
        # Тестируем установку сильного пароля
        try:
            auth_repo.set_password(test_user, 'N3wStr0ng_P@ssw0rd!')
            print("✅ Сильный пароль успешно установлен через AuthRepository")
        except ValidationError as e:
            print(f"❌ ОШИБКА: Сильный пароль отклонен AuthRepository: {e}")
        
        # Удаляем тестового пользователя
        test_user.delete()
        print("✅ Тестовый пользователь удален")
        
    except Exception as e:
        print(f"❌ Ошибка при создании тестового пользователя: {e}")
    
    print("\n=== Тестирование завершено ===")

if __name__ == '__main__':
    test_password_validation()