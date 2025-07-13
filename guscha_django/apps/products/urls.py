from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, ProductViewSet, 
    PreorderViewSet, WishlistViewSet
)

# Создаем роутер для API
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'preorders', PreorderViewSet)
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]