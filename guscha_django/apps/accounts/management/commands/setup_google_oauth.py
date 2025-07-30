from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Setup Google OAuth SocialApp'

    def handle(self, *args, **options):
        # Получаем Google OAuth настройки из переменных окружения
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not google_client_id or not google_client_secret:
            self.stdout.write(
                self.style.ERROR('GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET должны быть установлены в .env файле')
            )
            return
        
        # Проверяем существующий SocialApp для Google
        try:
            social_app = SocialApp.objects.get(provider='google')
            self.stdout.write(
                self.style.WARNING(f'Google SocialApp уже существует: {social_app.name}')
            )
            
            # Обновляем ключи если они изменились
            updated = False
            if social_app.client_id != google_client_id:
                social_app.client_id = google_client_id
                updated = True
                
            if social_app.secret != google_client_secret:
                social_app.secret = google_client_secret
                updated = True
                
            if updated:
                social_app.save()
                self.stdout.write(
                    self.style.SUCCESS('Google SocialApp обновлен с новыми ключами')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Google SocialApp уже настроен правильно')
                )
                
        except SocialApp.DoesNotExist:
            # Создаем новый SocialApp
            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=google_client_id,
                secret=google_client_secret
            )
            
            # Привязываем к текущему сайту
            site = Site.objects.get_current()
            social_app.sites.add(site)
            
            self.stdout.write(
                self.style.SUCCESS(f'Google SocialApp создан и привязан к сайту: {site.domain}')
            )
        
        # Проверяем привязку к сайту
        site = Site.objects.get_current()
        if not social_app.sites.filter(id=site.id).exists():
            social_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'Google SocialApp привязан к сайту: {site.domain}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n=== Google OAuth настройка завершена ===')
        )
        self.stdout.write(f'Provider: {social_app.provider}')
        self.stdout.write(f'Client ID: {social_app.client_id[:20]}...')
        self.stdout.write(f'Secret: {social_app.secret[:10]}...')
        self.stdout.write(f'Sites: {", ".join([s.domain for s in social_app.sites.all()])}')