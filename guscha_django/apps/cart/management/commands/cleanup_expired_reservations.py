from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.cart.models import Reservation


class Command(BaseCommand):
    """Команда для очистки истекших резервирований"""
    
    help = 'Очищает истекшие резервирования товаров'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать количество резервирований для удаления без фактического удаления',
        )
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        # Находим истекшие активные резервирования
        expired_reservations = Reservation.objects.filter(
            status='active',
            expires_at__lte=now
        )
        
        count = expired_reservations.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Найдено {count} истекших резервирований для очистки'
                )
            )
            return
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Истекших резервирований не найдено')
            )
            return
        
        # Обновляем статус истекших резервирований
        updated = expired_reservations.update(status='expired')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно обновлено {updated} истекших резервирований'
            )
        )