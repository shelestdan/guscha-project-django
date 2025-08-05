import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from apps.accounts.models import User

# Находим всех администраторов
admins = User.objects.filter(is_superuser=True)

print(f"Найдено администраторов: {admins.count()}")

for admin in admins:
    print(f"\nАдминистратор: {admin.email}")
    print(f"  ID: {admin.id}")
    print(f"  Telegram Chat ID: {admin.telegram_chat_id}")
    print(f"  Telegram Username: {admin.telegram_username}")
    print(f"  Telegram Verified: {admin.is_telegram_verified}")
    
    if admin.telegram_chat_id == 388199827 or admin.email == 'admin@guscha.com':
        print(f"  >>> Очищаем telegram_chat_id у {admin.email}")
        admin.telegram_chat_id = None
        admin.telegram_username = ""
        admin.is_telegram_verified = False
        admin.save()
        print("  >>> Telegram данные очищены!")

# Также проверим все коды верификации с этим chat_id
from apps.accounts.models import TelegramVerificationCode

codes = TelegramVerificationCode.objects.filter(telegram_chat_id='388199827')
print(f"\nНайдено кодов верификации с chat_id 388199827: {codes.count()}")

for code in codes:
    print(f"  Код ID: {code.id}, User: {code.user}, Type: {code.verification_type}, Used: {code.is_used}")
