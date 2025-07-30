from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, add_to_cart, add_preorder_to_cart, update_cart_item, remove_cart_item, clear_cart, create_cart_reservations

router = DefaultRouter()
router.register(r'items', CartViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('add/', add_to_cart, name='add-to-cart'),
    path('add_preorder/', add_preorder_to_cart, name='add-preorder-to-cart'),
    path('update/<int:item_id>/', update_cart_item, name='update-cart-item'),
    path('remove/<int:item_id>/', remove_cart_item, name='remove-cart-item'),
    path('clear/', clear_cart, name='clear-cart'),
    path('create-reservations/', create_cart_reservations, name='create-cart-reservations'),
]
