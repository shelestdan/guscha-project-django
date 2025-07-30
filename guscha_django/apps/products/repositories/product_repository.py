# -*- coding: utf-8 -*-
"""
Репозиторий для работы с товарами.

Этот модуль содержит методы для доступа к данным товаров.
"""

from django.db.models import Q, Prefetch
from ..models import Product, ProductImage, ProductReview


class ProductRepository:
    """
    Репозиторий для работы с товарами.
    
    Предоставляет методы для получения данных товаров из базы данных.
    """
    
    @staticmethod
    def get_active_products():
        """
        Получает все активные товары.
        
        Returns:
            QuerySet: Активные товары
        """
        return Product.objects.filter(is_active=True)
    
    @staticmethod
    def get_product_with_relations(product_id):
        """
        Получает товар со всеми связанными данными.
        
        Args:
            product_id: ID товара
            
        Returns:
            Product: Товар со связанными данными
        """
        return Product.objects.select_related(
            'category'
        ).prefetch_related(
            'product_images',
            'sizes',
            'reviews__user'
        ).get(id=product_id, is_active=True)
    
    @staticmethod
    def get_products_by_category(category, include_subcategories=False):
        """
        Получает товары по категории.
        
        Args:
            category: Категория
            include_subcategories: Включать подкатегории
            
        Returns:
            QuerySet: Товары категории
        """
        queryset = Product.objects.filter(is_active=True)
        
        if include_subcategories:
            # Получаем все подкатегории
            from ..models import Category
            subcategories = Category.objects.filter(
                parent=category,
                is_active=True
            )
            
            queryset = queryset.filter(
                Q(category=category) | Q(category__in=subcategories)
            )
        else:
            queryset = queryset.filter(category=category)
        
        return queryset
    
    @staticmethod
    def get_featured_products(limit=None):
        """
        Получает рекомендуемые товары.
        
        Args:
            limit: Максимальное количество товаров
            
        Returns:
            QuerySet: Рекомендуемые товары
        """
        queryset = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related('category').prefetch_related('product_images')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_products_in_stock():
        """
        Получает товары в наличии.
        
        Returns:
            QuerySet: Товары в наличии
        """
        return Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0
        )
    
    @staticmethod
    def search_products(query):
        """
        Поиск товаров по названию и описанию.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            QuerySet: Найденные товары
        """
        if not query:
            return Product.objects.none()
        
        return Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').prefetch_related('product_images')
    
    @staticmethod
    def get_products_by_price_range(min_price=None, max_price=None):
        """
        Получает товары в ценовом диапазоне.
        
        Args:
            min_price: Минимальная цена
            max_price: Максимальная цена
            
        Returns:
            QuerySet: Товары в ценовом диапазоне
        """
        queryset = Product.objects.filter(is_active=True)
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    @staticmethod
    def get_related_products(product, limit=4):
        """
        Получает похожие товары.
        
        Args:
            product: Товар
            limit: Максимальное количество товаров
            
        Returns:
            QuerySet: Похожие товары
        """
        return Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(
            id=product.id
        ).select_related('category').prefetch_related('product_images')[:limit]
    
    @staticmethod
    def get_product_images(product):
        """
        Получает изображения товара.
        
        Args:
            product: Товар
            
        Returns:
            QuerySet: Изображения товара
        """
        return ProductImage.objects.filter(
            product=product
        ).order_by('-is_primary', 'order', 'id')
    
    @staticmethod
    def get_product_reviews(product, limit=None):
        """
        Получает отзывы о товаре.
        
        Args:
            product: Товар
            limit: Максимальное количество отзывов
            
        Returns:
            QuerySet: Отзывы о товаре
        """
        queryset = ProductReview.objects.filter(
            product=product
        ).select_related('user').order_by('-created_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_optimized_queryset():
        """
        Получает оптимизированный queryset для списка товаров.
        
        Returns:
            QuerySet: Оптимизированный queryset
        """
        return Product.objects.select_related(
            'category'
        ).prefetch_related(
            Prefetch(
                'product_images',
                queryset=ProductImage.objects.filter(is_primary=True),
                to_attr='primary_images'
            ),
            'sizes'
        ).filter(is_active=True)