"""URL configuration for Telegram bot (без админки)."""

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy', 'service': 'telegram-bot'})

urlpatterns = [
    # Health check endpoint
    path('health/', health_check, name='health_check'),
    
    # API маршруты для Telegram бота
    path('api/products/', include('apps.products.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/addresses/', include('apps.addresses.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Telegram bot маршруты
    path('telegram/', include('telegram_bot.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)