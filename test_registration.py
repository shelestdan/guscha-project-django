#!/usr/bin/env python3
import requests
import json

# Тестируем API регистрации
url = 'http://127.0.0.1:8000/api/accounts/users/'

# Данные для регистрации с password_confirm
data = {
    'username': 'testuser123',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'phone': '+1234567890',
    'password': 'TestPassword123!',
    'password_confirm': 'TestPassword123!'  # Добавляем поле подтверждения пароля
}

print("Отправляем данные регистрации:")
print(json.dumps(data, indent=2, ensure_ascii=False))

try:
    response = requests.post(url, json=data)
    print(f"\nСтатус ответа: {response.status_code}")
    print(f"Ответ сервера: {response.text}")
    
    if response.status_code == 201:
        print("✅ Регистрация прошла успешно!")
    else:
        print("❌ Ошибка регистрации")
        
except Exception as e:
    print(f"Ошибка при отправке запроса: {e}")