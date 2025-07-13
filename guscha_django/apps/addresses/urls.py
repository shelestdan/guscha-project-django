from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddressViewSet

# Создаем router для ViewSet
router = DefaultRouter()
router.register(r'', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]