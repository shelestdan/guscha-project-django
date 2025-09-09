"""
URL configuration for guscha_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.static import serve
from apps.accounts.views import qr_trigger
import os

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy', 'service': 'django'})

def robots_txt(request):
    """Serve robots.txt from config directory"""
    robots_path = os.path.join(settings.BASE_DIR, 'config', 'robots.txt')
    return serve(request, os.path.basename(robots_path), document_root=os.path.dirname(robots_path))

urlpatterns = [
    # Health check endpoint
    path('health/', health_check, name='health_check'),
    
    # Robots.txt from config directory
    path('robots.txt', robots_txt, name='robots_txt'),
    
    # ============================================================================
    # SECURITY URLS - ГОТОВОЕ РЕШЕНИЕ ДЛЯ БЕЗОПАСНОСТИ
    # ============================================================================
    
    # Стандартная админка Django
    path('admin/', admin.site.urls),
    
    # API маршруты
    path('api/products/', include('apps.products.urls')),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/cart/', include('apps.cart.urls')),
    path('api/addresses/', include('apps.addresses.urls')),
    path('api/collections/', include('apps.collections.urls')),
    path('api/background/', include('apps.background_content.urls')),
    # path('security/', include('apps.security.urls')),  # Удалено - заменено на django-allauth + dj-rest-auth
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/social/', include('allauth.urls')),

    path('api/admin/', include('apps.core.urls')),  # API для админки
    path('api/backup/', include('apps.backup_system.urls')),  # Система резервного копирования
    
    # Django Silk профилирование (только в DEBUG режиме)
    *([path('silk/', include('silk.urls', namespace='silk'))] if settings.DEBUG else []),
    
    # Server-Sent Events (закомментировано - пакет не установлен)
    # path('events/', include('django_eventstream.urls')),
    
    # Дополнительные API маршруты для совместимости с фронтендом
    path('api/preorders/', include(('apps.products.urls', 'products'), namespace='api-preorders')),
    path('api/public/', include(('apps.core.urls', 'core'), namespace='api-public-core')),
    
    # QR-trigger маршрут (должен быть перед catch-all)
    path('qr-trigger/<uuid:qr_id>/', qr_trigger, name='qr_trigger'),
    
    # Основные маршруты приложения
    path('', include(('apps.core.urls', 'core'), namespace='main')),
    
    # React-приложение должно быть последним (catch-all)
    # Исключаем admin, api, media и qr-trigger из перехвата React-приложением
    re_path(r'^(?!admin|api|media|static|qr-trigger).*$', TemplateView.as_view(template_name='index.html'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
