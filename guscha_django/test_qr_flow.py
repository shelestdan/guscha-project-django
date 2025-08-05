import os
import django
from datetime import datetime, timezone

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from apps.accounts.models import TelegramVerificationCode, QRCodeScan, PendingUserRegistration
from apps.accounts.services.telegram_service import TelegramService

def test_qr_registration_flow():
    """Тестирует полный процесс QR-регистрации"""
    print("=== Тест QR-регистрации ===")
    
    # Очищаем старые тестовые записи
    test_email = "test@example.com"
    PendingUserRegistration.objects.filter(email=test_email).delete()
    print("Очищены старые тестовые записи")
    
    # Создаем pending registration
    pending_reg = PendingUserRegistration.objects.create(
        email=test_email,
        phone="+79123456789",
        first_name="Тест",
        last_name="Пользователь"
    )
    print(f"Создана pending registration: {pending_reg.email}")
    
    # Создаем код верификации для QR-регистрации
    telegram_service = TelegramService()
    verification_code = telegram_service.create_verification_code(
        telegram_chat_id=None,  # Для QR-регистрации может быть None
        verification_type='qr_registration',
        pending_registration=pending_reg
    )
    print(f"Создан код верификации: {verification_code.id}")
    print(f"Код истекает: {verification_code.expires_at}")
    print(f"Текущее время: {datetime.now(timezone.utc)}")
    print(f"Код действителен: {verification_code.is_valid()}")
    
    # Создаем QR-код
    qr_code = QRCodeScan.objects.create(
        verification_code=verification_code,
        pending_registration=pending_reg,
        trigger_url=f"/qr-trigger/{verification_code.id}/",
        telegram_bot_url=f"https://t.me/your_bot?start={verification_code.id}"
    )
    print(f"Создан QR-код: {qr_code.qr_id}")
    
    # Симулируем сканирование QR-кода
    qr_code.scanned_at = datetime.now(timezone.utc)
    qr_code.trigger_activated_at = datetime.now(timezone.utc)
    qr_code.save()
    print("QR-код отмечен как отсканированный")
    
    # Проверяем код после создания
    verification_code.refresh_from_db()
    print(f"\nПроверка кода после создания:")
    print(f"ID: {verification_code.id}")
    print(f"Тип: {verification_code.verification_type}")
    print(f"Создан: {verification_code.created_at}")
    print(f"Истекает: {verification_code.expires_at}")
    print(f"Использован: {verification_code.is_used}")
    print(f"Истек: {verification_code.is_expired()}")
    print(f"Действителен: {verification_code.is_valid()}")
    
    # Генерируем код для отображения
    display_code = verification_code.generate_secure_code()
    print(f"Код для отображения: {display_code}")
    
    return verification_code, qr_code

if __name__ == "__main__":
    test_qr_registration_flow()