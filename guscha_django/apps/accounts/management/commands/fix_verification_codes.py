from django.core.management.base import BaseCommand
from apps.accounts.models import TelegramVerificationCode

class Command(BaseCommand):
    help = 'Пересохранить существующие коды верификации для правильного хеширования'
    
    def handle(self, *args, **options):
        codes = TelegramVerificationCode.objects.filter(
            verification_type='qr_registration', 
            is_used=False
        )
        
        self.stdout.write(f'Найдено {codes.count()} неиспользованных QR кодов')
        
        fixed_count = 0
        for code in codes:
            old_hash = code.code_hash[:10] if code.code_hash else 'None'
            original_code = code.code
            
            # Пересохраняем код для правильного хеширования
            code.save()
            
            # Проверяем результат
            verify_result = code.verify_code(original_code)
            self.stdout.write(f'ID {code.id}: {old_hash}... -> {code.code_hash[:10]}... verify: {verify_result}')
            
            if verify_result:
                fixed_count += 1
            else:
                self.stdout.write(f'  ⚠️  Код {code.id} все еще не верифицируется!')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Исправлено {fixed_count} из {codes.count()} кодов'))