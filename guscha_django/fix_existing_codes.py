#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_django.settings')
django.setup()

from apps.accounts.models import TelegramVerificationCode

def fix_existing_codes():
    """Пересохранить существующие коды для правильного хеширования"""
    codes = TelegramVerificationCode.objects.filter(
        verification_type='qr_registration', 
        is_used=False
    )
    
    print(f'Найдено {codes.count()} неиспользованных QR кодов')
    
    for code in codes:
        old_hash = code.code_hash[:10] if code.code_hash else 'None'
        original_code = code.code
        
        # Пересохраняем код для правильного хеширования
        code.save()
        
        # Проверяем результат
        verify_result = code.verify_code(original_code)
        print(f'ID {code.id}: {old_hash}... -> {code.code_hash[:10]}... verify: {verify_result}')
        
        if not verify_result:
            print(f'  ⚠️  Код {code.id} все еще не верифицируется!')
    
    print('\n✅ Пересохранение завершено')

if __name__ == '__main__':
    fix_existing_codes()