import os
import django
from datetime import datetime, timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from apps.accounts.models import TelegramVerificationCode, QRCodeScan

# Получаем последний созданный код верификации
latest_code = TelegramVerificationCode.objects.filter(
    verification_type='qr_registration'
).order_by('-created_at').first()

if latest_code:
    current_time = datetime.now(timezone.utc)
    print(f"Код верификации ID: {latest_code.id}")
    print(f"Код: {latest_code.code}")
    print(f"Создан: {latest_code.created_at}")
    print(f"Истекает: {latest_code.expires_at}")
    print(f"Текущее время: {current_time}")
    print(f"Разница (секунды): {(latest_code.expires_at - current_time).total_seconds()}")
    print(f"Истек ли код: {latest_code.is_expired()}")
    print(f"Использован ли код: {latest_code.is_used}")
    print(f"Действителен ли код: {latest_code.is_valid()}")
    
    # Проверим связанный QR-код
    qr_code = QRCodeScan.objects.filter(verification_code=latest_code).first()
    if qr_code:
        print(f"\nQR-код ID: {qr_code.qr_id}")
        print(f"QR создан: {qr_code.created_at}")
        print(f"QR отсканирован: {qr_code.scanned_at}")
        print(f"Триггер активирован: {qr_code.trigger_activated_at}")
        print(f"Бот запущен: {qr_code.bot_started_at}")
else:
    print("Код верификации не найден")