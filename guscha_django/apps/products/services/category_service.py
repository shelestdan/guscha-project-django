# -*- coding: utf-8 -*-
"""
Сервис для работы с категориями товаров.

Этот модуль содержит бизнес-логику для управления категориями.
"""

from django.db.models import Count, Q
from ..models import Category
import logging

logger = logging.getLogger(__name__)


class CategoryService:
    """
    Сервис для работы с категориями товаров.
    
    Предоставляет методы для получения и фильтрации категорий.
    """
    
    def get_filtered_categories(self, filters=None):
        """
        Получает отфильтрованные категории.
        
        Args:
            filters: Словарь с фильтрами
            
        Returns:
            QuerySet: Отфильтрованный queryset категорий
        """
        queryset = Category.objects.filter(is_active=True)
        
        if filters:
            # Фильтр по родительской категории
            if 'parent' in filters:
                if filters['parent'] is None:
                    queryset = queryset.filter(parent__isnull=True)
                else:
                    queryset = queryset.filter(parent=filters['parent'])
            
            # Фильтр по наличию товаров
            if 'has_products' in filters and filters['has_products']:
                queryset = queryset.annotate(
                    product_count=Count('products', filter=Q(products__is_active=True))
                ).filter(product_count__gt=0)
            
            # Фильтр по уровню вложенности
            if 'level' in filters:
                if filters['level'] == 0:
                    queryset = queryset.filter(parent__isnull=True)
                elif filters['level'] == 1:
                    queryset = queryset.filter(parent__isnull=False, parent__parent__isnull=True)
        
        return queryset.order_by('order', 'name')
    
    def get_category_tree(self):
        """
        Получает дерево категорий.
        
        Returns:
            list: Список категорий с вложенными подкатегориями
        """
        try:
            # Получаем все активные категории
            categories = Category.objects.filter(is_active=True).order_by('order', 'name')
            
            # Строим дерево
            category_dict = {}
            root_categories = []
            
            # Создаем словарь всех категорий
            for category in categories:
                category_dict[category.id] = {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'image': category.image.url if category.image else None,
                    'parent_id': category.parent_id,
                    'children': []
                }
            
            # Строим дерево
            for category_data in category_dict.values():
                if category_data['parent_id'] is None:
                    root_categories.append(category_data)
                else:
                    parent = category_dict.get(category_data['parent_id'])
                    if parent:
                        parent['children'].append(category_data)
            
            return root_categories
            
        except Exception as e:
            logger.error(f'Ошибка при построении дерева категорий: {e}')
            return []
    
    def get_category_breadcrumbs(self, category):
        """
        Получает хлебные крошки для категории.
        
        Args:
            category: Экземпляр категории
            
        Returns:
            list: Список категорий от корня до текущей
        """
        breadcrumbs = []
        current = category
        
        while current:
            breadcrumbs.insert(0, {
                'id': current.id,
                'name': current.name,
                'slug': current.slug
            })
            current = current.parent
        
        return breadcrumbs
    
    def get_popular_categories(self, limit=10):
        """
        Получает популярные категории по количеству товаров.
        
        Args:
            limit: Максимальное количество категорий
            
        Returns:
            QuerySet: Популярные категории
        """
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).filter(
            product_count__gt=0
        ).order_by('-product_count')[:limit]
    
    def search_categories(self, query):
        """
        Поиск категорий по названию и описанию.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            QuerySet: Найденные категории
        """
        if not query:
            return Category.objects.none()
        
        return Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).order_by('name')
    
    def get_category_statistics(self, category_id):
        """
        Получает статистику по категории.
        
        Args:
            category_id: ID категории
            
        Returns:
            dict: Статистика категории
        """
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            
            # Подсчитываем товары в категории и подкатегориях
            from ..models import Product
            
            # Получаем все подкатегории
            subcategories = Category.objects.filter(
                parent=category,
                is_active=True
            )
            
            # Товары в текущей категории
            products_count = Product.objects.filter(
                category=category,
                is_active=True
            ).count()
            
            # Товары в подкатегориях
            subcategory_products_count = Product.objects.filter(
                category__in=subcategories,
                is_active=True
            ).count()
            
            return {
                'category_id': category.id,
                'category_name': category.name,
                'products_count': products_count,
                'subcategories_count': subcategories.count(),
                'subcategory_products_count': subcategory_products_count,
                'total_products_count': products_count + subcategory_products_count
            }
            
        except Category.DoesNotExist:
            return {
                'error': 'Категория не найдена'
            }
        except Exception as e:
            logger.error(f'Ошибка при получении статистики категории: {e}')
            return {
                'error': 'Ошибка при получении статистики'
            }