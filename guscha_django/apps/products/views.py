# Импортируем сервисы для работы с изображениями
from .services.image_service import ImageService
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.admin.views.decorators import staff_member_required

# Создаем экземпляр сервиса
image_service = ImageService()

@staff_member_required
@csrf_protect
def upload_product_image(request):
    """Загрузка изображений товара через сервис"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        files = request.FILES.getlist('images')
        uploaded_images = image_service.upload_multiple_images(files)
        return JsonResponse({'success': True, 'images': uploaded_images})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def get_product_images(request, product_id):
    """Получение списка изображений товара через сервис"""
    try:
        images_data = image_service.get_product_images(product_id)
        return JsonResponse({'success': True, 'images': images_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@csrf_protect
def reorder_product_images(request):
    """Изменение порядка изображений товара через сервис"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        image_order = data.get('order', [])
        image_service.reorder_images(image_order)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@csrf_protect
def set_primary_image(request):
    """Установка основного изображения товара через сервис"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        image_id = data.get('image_id')
        image_service.set_primary_image(image_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.db.models import Avg, Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
import os
import base64
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import json

from .models import (
    Category, Product, ProductImage, ProductSize, 
    ProductVariant, ProductReview, Preorder, PreorderSize, Wishlist
)
from .serializers import (
    CategorySerializer, CategoryListSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, ProductUpdateSerializer,
    ProductImageSerializer, ProductSizeSerializer,
    ProductReviewSerializer, ProductReviewCreateSerializer,
    PreorderListSerializer, PreorderDetailSerializer, WishlistSerializer,
    PreorderSizeSerializer
)
from .filters import ProductFilter
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from .pagination import StandardResultsSetPagination

# Импортируем сервисы и репозитории
from .services.product_service import ProductService
from .services.category_service import CategoryService
from .repositories.product_repository import ProductRepository
from .repositories.category_repository import CategoryRepository

# Создаем экземпляры сервисов
product_service = ProductService()
category_service = CategoryService()


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с категориями товаров"""
    queryset = Category.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order']
    ordering = ['sort_order', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_queryset(self):
        # Используем сервис для получения категорий с фильтрацией
        filters = {
            'is_active': self.request.query_params.get('is_active'),
            'parent': self.request.query_params.get('parent')
        }
        return category_service.get_filtered_categories(filters)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с товарами"""
    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku', 'search_keywords']
    ordering_fields = ['name', 'price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        return ProductDetailSerializer
        
    def get_serializer_context(self):
        """Добавление request в контекст сериализатора"""
        context = super().get_serializer_context()
        return context
    
    def get_queryset(self):
        # Используем сервис для получения оптимизированного queryset
        filters = {
            'is_active': self.request.query_params.get('is_active'),
            'is_featured': self.request.query_params.get('is_featured'),
            'in_stock': self.request.query_params.get('in_stock')
        }
        return product_service.get_optimized_queryset(filters)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Получение отзывов о товаре"""
        product = self.get_object()
        reviews = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_review(self, request, slug=None):
        """Добавление отзыва о товаре через сервис"""
        product = self.get_object()
        
        try:
            review_data = product_service.add_review(
                product=product,
                user=request.user,
                review_data=request.data
            )
            return Response(review_data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request, slug=None):
        """Добавление товара в список желаний через сервис"""
        product = self.get_object()
        
        try:
            product_service.add_to_wishlist(request.user, product)
            return Response(
                {"detail": "Товар добавлен в список желаний"},
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_from_wishlist(self, request, slug=None):
        """Удаление товара из списка желаний через сервис"""
        product = self.get_object()
        
        try:
            product_service.remove_from_wishlist(request.user, product)
            return Response(
                {"detail": "Товар удален из списка желаний"},
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


class PreorderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с предзаказами (только чтение)"""
    queryset = Preorder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PreorderDetailSerializer
        return PreorderListSerializer
    
    def get_queryset(self):
        queryset = Preorder.objects.all()
        
        # Фильтрация по активным предзаказам
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            if is_active:
                queryset = queryset.filter(is_active=True)
            else:
                queryset = queryset.filter(is_active=False)
        
        # Фильтрация по рекомендуемым предзаказам (для hero блока)
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            is_featured = is_featured.lower() == 'true'
            if is_featured:
                queryset = queryset.filter(is_featured=True)
            else:
                queryset = queryset.filter(is_featured=False)
        
        # Ограничение количества результатов
        limit = self.request.query_params.get('limit')
        if limit is not None:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        
        return queryset


class WishlistViewSet(viewsets.GenericViewSet):
    """ViewSet для работы со списком желаний пользователя"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def list(self, request):
        """Получение списка желаний пользователя"""
        wishlist_items = Wishlist.objects.filter(user=request.user)\
            .select_related('product', 'product__category')\
            .prefetch_related(
                Prefetch('product__product_images', queryset=ProductImage.objects.filter(is_primary=True)[:1])
            )
        
        page = self.paginate_queryset(wishlist_items)
        if page is not None:
            serializer = WishlistSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = WishlistSerializer(wishlist_items, many=True, context={'request': request})
        return Response(serializer.data)
    
    def create(self, request):
        """Добавление товара в список желаний"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {"detail": "Не указан ID товара"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Товар не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, есть ли уже этот товар в списке желаний
        if Wishlist.objects.filter(user=request.user, product=product).exists():
            return Response(
                {"detail": "Товар уже в списке желаний"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Добавляем товар в список желаний
        wishlist_item = Wishlist.objects.create(user=request.user, product=product)
        serializer = WishlistSerializer(wishlist_item, context={'request': request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['delete'])
    def remove(self, request):
        """Удаление товара из списка желаний"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {"detail": "Не указан ID товара"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, есть ли товар в списке желаний
        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).first()
        
        if not wishlist_item:
            return Response(
                {"detail": "Товар не найден в списке желаний"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Удаляем товар из списка желаний
        wishlist_item.delete()
        return Response(
            {"detail": "Товар удален из списка желаний"},
            status=status.HTTP_200_OK
        )
