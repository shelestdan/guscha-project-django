from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, ProductViewSet, 
    PreorderViewSet, WishlistViewSet,
    upload_product_image, get_product_images,
    reorder_product_images, set_primary_image
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
    
    # Admin AJAX endpoints
    path('admin/upload-image/', upload_product_image, name='admin_upload_image'),
    path('admin/product/<int:product_id>/images/', get_product_images, name='admin_get_product_images'),
    path('admin/reorder-images/', reorder_product_images, name='admin_reorder_images'),
    path('admin/set-primary-image/', set_primary_image, name='admin_set_primary_image'),
    

]
