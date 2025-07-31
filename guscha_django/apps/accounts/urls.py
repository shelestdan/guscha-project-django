from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

# Создаем роутер для ViewSet'ов
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

app_name = 'accounts'

urlpatterns = [
    # Включаем маршруты роутера
    path('', include(router.urls)),
    
    # === Аутентификация ===
    # CSRF токен
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
    
    # JWT токены
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Основные действия аутентификации (через UserViewSet)
    # POST /api/accounts/users/login/ - вход
    # POST /api/accounts/users/logout/ - выход
    # GET /api/accounts/users/me/ - текущий пользователь
    # PUT /api/accounts/users/me/ - обновление профиля
    # POST /api/accounts/users/change_password/ - смена пароля
    
    # === Сброс пароля ===
    path('password-reset/', 
         views.password_reset_request, 
         name='password_reset_request'),
    path('password-reset/confirm/', 
         views.password_reset_confirm, 
         name='password_reset_confirm'),
    
    # === Telegram интеграция ===
    # Статус бота
    path('telegram/bot/status/', 
         views.telegram_bot_status, 
         name='telegram_bot_status'),
    
    # Активация через Telegram
    path('telegram/activate/', 
         views.telegram_bot_activate, 
         name='telegram_activate'),
    
    # Верификация кода
    path('telegram/verify/', 
         views.telegram_verify_code, 
         name='telegram_verify'),
    
    # Сброс пароля через Telegram
    path('telegram/password-reset/', 
         views.telegram_password_reset_request, 
         name='telegram_password_reset_request'),
    path('telegram/password-reset/confirm/', 
         views.telegram_password_reset_confirm, 
         name='telegram_password_reset_confirm'),
    
    # Привязка/отвязка Telegram аккаунта
    path('telegram/link/', 
         views.link_telegram, 
         name='telegram_link'),
    path('telegram/unlink/', 
         views.unlink_telegram, 
         name='telegram_unlink'),
    
    # === QR коды ===
    # Создание QR кода
    path('qr/create/', 
         views.create_qr_code, 
         name='qr_create'),
    
    # Триггер QR кода (сканирование) - этот маршрут обрабатывается в основном urls.py
    # path('qr/<str:qr_code>/trigger/', views.qr_trigger, name='qr_trigger'),
    
    # Статус QR кода
    path('qr/status/<str:qr_id>/', 
         views.qr_status, 
         name='qr_status'),
    
    # Отметка старта бота через QR
    path('qr/bot-started/', 
         views.qr_bot_started, 
         name='qr_bot_started'),
    
    # === Статистика и дополнительные функции ===
    # Статистика пользователя
    path('users/statistics/', 
         views.user_statistics, 
         name='user_statistics'),
    
    # === Административные маршруты ===
    # Список всех пользователей (только для админов)
    # GET /api/accounts/users/ - список пользователей
    # POST /api/accounts/users/ - создание пользователя
    # GET /api/accounts/users/{id}/ - конкретный пользователь
    # PUT /api/accounts/users/{id}/ - обновление пользователя
    # DELETE /api/accounts/users/{id}/ - удаление пользователя
    
    # === Дополнительные API endpoints ===
    # ВРЕМЕННО ОТКЛЮЧЕНО: Отсутствуют соответствующие view-классы
    # path('check-email/', 
    #      views.CheckEmailAvailabilityView.as_view(), 
    #      name='check_email'),
    # 
    # path('check-password-strength/', 
    #      views.CheckPasswordStrengthView.as_view(), 
    #      name='check_password_strength'),
    # 
    # path('security-settings/', 
    #      views.SecuritySettingsView.as_view(), 
    #      name='security_settings'),
    # 
    # path('security-events/', 
    #      views.SecurityEventsView.as_view(), 
    #      name='security_events'),
    # 
    # === Webhook endpoints ===
    # ВРЕМЕННО ОТКЛЮЧЕНО: Отсутствуют соответствующие view-классы
    # path('webhook/telegram/', 
    #      views.TelegramWebhookView.as_view(), 
    #      name='telegram_webhook'),
    # 
    # === Утилитарные endpoints ===
    # ВРЕМЕННО ОТКЛЮЧЕНО: Отсутствуют соответствующие view-классы
    # path('health/', 
    #      views.HealthCheckView.as_view(), 
    #      name='health_check'),
    # 
    # path('version/', 
    #      views.APIVersionView.as_view(), 
    #      name='api_version'),
]

# Дополнительные маршруты для разработки (только в DEBUG режиме)
# ВРЕМЕННО ОТКЛЮЧЕНО: Отсутствуют соответствующие view-классы
# from django.conf import settings
# if settings.DEBUG:
#     urlpatterns += [
#         # Тестовые endpoints
#         path('test/email/', 
#              views.TestEmailView.as_view(), 
#              name='test_email'),
#         path('test/telegram/', 
#              views.TestTelegramView.as_view(), 
#              name='test_telegram'),
#         path('test/qr/', 
#              views.TestQRView.as_view(), 
#              name='test_qr'),
#     ]

# Документация по API маршрутам:
"""
Основные группы маршрутов:

1. ПОЛЬЗОВАТЕЛИ (UserViewSet):
   - GET /api/accounts/users/ - список пользователей (админ)
   - POST /api/accounts/users/ - создание пользователя
   - GET /api/accounts/users/{id}/ - получение пользователя
   - PUT /api/accounts/users/{id}/ - обновление пользователя
   - DELETE /api/accounts/users/{id}/ - удаление пользователя
   - POST /api/accounts/users/login/ - вход в систему
   - POST /api/accounts/users/logout/ - выход из системы
   - GET /api/accounts/users/me/ - текущий пользователь
   - PUT /api/accounts/users/me/ - обновление профиля
   - POST /api/accounts/users/change_password/ - смена пароля

2. АУТЕНТИФИКАЦИЯ:
   - POST /api/accounts/auth/token/ - получение JWT токена
   - POST /api/accounts/auth/token/refresh/ - обновление токена
   - POST /api/accounts/auth/token/verify/ - проверка токена
   - POST /api/accounts/password-reset/ - запрос сброса пароля
   - POST /api/accounts/password-reset/confirm/ - подтверждение сброса

3. TELEGRAM ИНТЕГРАЦИЯ:
   - GET /api/accounts/telegram/bot/status/ - статус бота
   - POST /api/accounts/telegram/activate/ - активация через Telegram
   - POST /api/accounts/telegram/verify/ - верификация кода
   - POST /api/accounts/telegram/password-reset/ - сброс пароля через Telegram
   - POST /api/accounts/telegram/password-reset/confirm/ - подтверждение сброса
   - POST /api/accounts/telegram/link/ - привязка аккаунта
   - POST /api/accounts/telegram/unlink/ - отвязка аккаунта
   - POST /api/accounts/webhook/telegram/ - webhook для бота

4. QR КОДЫ:
   - POST /api/accounts/qr/create/ - создание QR кода
   - POST /api/accounts/qr/{code}/trigger/ - сканирование QR кода
   - GET /api/accounts/qr/{code}/status/ - статус QR кода
   - POST /api/accounts/qr/{code}/bot-start/ - отметка старта бота

5. СТАТИСТИКА И УТИЛИТЫ:
   - GET /api/accounts/users/statistics/ - статистика пользователя
   - POST /api/accounts/check-email/ - проверка доступности email
   - POST /api/accounts/check-password-strength/ - проверка силы пароля
   - GET /api/accounts/security-settings/ - настройки безопасности
   - GET /api/accounts/security-events/ - события безопасности
   - GET /api/accounts/health/ - проверка состояния сервиса
   - GET /api/accounts/version/ - версия API

6. ТЕСТОВЫЕ (только в DEBUG):
   - POST /api/accounts/test/email/ - тест отправки email
   - POST /api/accounts/test/telegram/ - тест Telegram интеграции
   - POST /api/accounts/test/qr/ - тест QR функциональности

Все маршруты поддерживают соответствующие HTTP методы и возвращают
JSON ответы в стандартном формате Django REST Framework.
"""