#!/usr/bin/env python3
"""
Скрипт для генерации секретных ключей для Django проекта
Использование: python generate-secrets.py
"""

import secrets
import string
from django.core.management.utils import get_random_secret_key

def generate_strong_password(length=32):
    """Генерирует сильный пароль"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def generate_admin_url():
    """Генерирует случайный путь для админки"""
    words = ['secure', 'private', 'hidden', 'secret', 'admin', 'panel', 'control', 'manage']
    random_word = secrets.choice(words)
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for i in range(8))
    return f"{random_word}-{random_suffix}/"

def main():
    print("=" * 60)
    print("Генератор секретных ключей для Guscha Project")
    print("=" * 60)
    print()
    
    print("📝 Скопируйте эти значения в ваш .env файл:")
    print()
    
    # Django Secret Key
    django_secret = get_random_secret_key()
    print(f"SECRET_KEY={django_secret}")
    print()
    
    # JWT Secret Key
    jwt_secret = get_random_secret_key()
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    # PostgreSQL Password
    postgres_password = generate_strong_password(32)
    print(f"POSTGRES_PASSWORD={postgres_password}")
    print()
    
    # Admin URL
    admin_url = generate_admin_url()
    print(f"ADMIN_URL={admin_url}")
    print()
    
    print("=" * 60)
    print("⚠️  ВАЖНО:")
    print("1. Сохраните эти ключи в безопасном месте")
    print("2. НЕ коммитьте .env файл в git")
    print("3. Используйте разные ключи для разных окружений")
    print("=" * 60)
    print()
    
    # Дополнительные рекомендации
    print("💡 Дополнительные рекомендации:")
    print()
    print("Email пароль:")
    email_password = generate_strong_password(24)
    print(f"EMAIL_HOST_PASSWORD={email_password}")
    print()
    
    print("Antibot Session Secret (32 символа):")
    antibot_secret = generate_strong_password(32)
    print(f"ANTIBOT_SESSION_SECRET={antibot_secret}")
    print()

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("⚠️  Django не установлен. Устанавливаю...")
        print()
        print("Альтернативный метод генерации:")
        print()
        
        # Альтернативная генерация без Django
        import secrets
        import string
        
        def alt_secret_key(length=50):
            chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
            return ''.join(secrets.choice(chars) for i in range(length))
        
        print(f"SECRET_KEY={alt_secret_key()}")
        print()
        print(f"JWT_SECRET_KEY={alt_secret_key()}")
        print()
        print(f"POSTGRES_PASSWORD={generate_strong_password(32)}")
        print()
        print(f"ADMIN_URL={generate_admin_url()}")
        print()
