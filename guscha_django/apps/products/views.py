from django.db.models import Avg, Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

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
        queryset = Category.objects.all()
        
        # Фильтрация по активности
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Фильтрация по родительской категории
        parent = self.request.query_params.get('parent')
        if parent is not None:
            if parent == 'null':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__slug=parent)
        
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с товарами"""
    queryset = Product.objects.all()
    permission_classes = [IsAdminOrReadOnly]
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
        queryset = Product.objects.all()
        
        # Оптимизация запросов для списка товаров
        if self.action == 'list':
            queryset = queryset.select_related('category')\
                .prefetch_related(
                    Prefetch('product_images', queryset=ProductImage.objects.filter(is_primary=True))
                )\
                .annotate(
                    avg_rating_annotated=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                    review_count_annotated=Count('reviews', filter=Q(reviews__is_approved=True))
                )
        
        # Оптимизация запросов для детального представления товара
        elif self.action == 'retrieve':
            queryset = queryset.select_related('category')\
                .prefetch_related(
                    'product_images',
                    'sizes',
                    'variants',
                    Prefetch('reviews', queryset=ProductReview.objects.filter(is_approved=True))
                )\
                .annotate(
                    avg_rating_annotated=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                    review_count_annotated=Count('reviews', filter=Q(reviews__is_approved=True))
                )
        
        # Фильтрация по активности
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Фильтрация по рекомендуемым товарам
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            is_featured = is_featured.lower() == 'true'
            queryset = queryset.filter(is_featured=is_featured)
        
        # Фильтрация по наличию на складе
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            in_stock = in_stock.lower() == 'true'
            if in_stock:
                queryset = queryset.filter(
                    Q(track_inventory=False) | 
                    Q(stock_quantity__gt=0) | 
                    Q(allow_backorder=True)
                )
            else:
                queryset = queryset.filter(
                    track_inventory=True,
                    stock_quantity=0,
                    allow_backorder=False
                )
        
        return queryset
    
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
        """Добавление отзыва о товаре"""
        product = self.get_object()
        
        # Проверка на существование отзыва от этого пользователя
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user
        ).first()
        
        if existing_review:
            return Response(
                {"detail": "Вы уже оставляли отзыв на этот товар"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_wishlist(self, request, slug=None):
        """Добавление товара в список желаний"""
        product = self.get_object()
        user = request.user
        
        # Проверяем, есть ли уже этот товар в списке желаний
        if user.wishlist_items.filter(product=product).exists():
            return Response(
                {"detail": "Товар уже в списке желаний"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Добавляем товар в список желаний
        user.wishlist_items.create(product=product)
        return Response(
            {"detail": "Товар добавлен в список желаний"},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_from_wishlist(self, request, slug=None):
        """Удаление товара из списка желаний"""
        product = self.get_object()
        user = request.user
        
        # Проверяем, есть ли товар в списке желаний
        wishlist_item = user.wishlist_items.filter(product=product).first()
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


class PreorderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с предзаказами (только чтение)"""
    queryset = Preorder.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'start_date', 'end_date']
    ordering = ['-start_date']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PreorderDetailSerializer
        return PreorderListSerializer
    
    def get_queryset(self):
        queryset = Preorder.objects.all()
        
        # Фильтрация по активным предзаказам
        now = timezone.now()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            if is_active:
                queryset = queryset.filter(
                    start_date__lte=now,
                    end_date__gte=now,
                    is_active=True
                )
            else:
                queryset = queryset.filter(
                    Q(end_date__lt=now) | 
                    Q(is_active=False)
                )
        
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
