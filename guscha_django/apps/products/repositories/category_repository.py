# -*- coding: utf-8 -*-
"""
Репозиторий для работы с категориями.

Этот модуль содержит методы для доступа к данным категорий.
"""

from django.db.models import Q, Count
from ..models import Category


class CategoryRepository:
    """
    Репозиторий для работы с категориями.
    
    Предоставляет методы для получения данных категорий из базы данных.
    """
    
    @staticmethod
    def get_active_categories():
        """
        Получает все активные категории.
        
        Returns:
            QuerySet: Активные категории
        """
        return Category.objects.filter(is_active=True)
    
    @staticmethod
    def get_root_categories():
        """
        Получает корневые категории (без родителя).
        
        Returns:
            QuerySet: Корневые категории
        """
        return Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).order_by('order', 'name')
    
    @staticmethod
    def get_subcategories(parent_category):
        """
        Получает подкатегории для указанной категории.
        
        Args:
            parent_category: Родительская категория
            
        Returns:
            QuerySet: Подкатегории
        """
        return Category.objects.filter(
            is_active=True,
            parent=parent_category
        ).order_by('order', 'name')
    
    @staticmethod
    def get_category_by_slug(slug):
        """
        Получает категорию по slug.
        
        Args:
            slug: Slug категории
            
        Returns:
            Category: Категория
        """
        return Category.objects.get(
            slug=slug,
            is_active=True
        )
    
    @staticmethod
    def get_categories_with_product_count():
        """
        Получает категории с количеством товаров.
        
        Returns:
            QuerySet: Категории с аннотацией product_count
        """
        return Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count(
                'products',
                filter=Q(products__is_active=True)
            )
        ).order_by('order', 'name')
    
    @staticmethod
    def get_categories_with_products():
        """
        Получает только категории, в которых есть товары.
        
        Returns:
            QuerySet: Категории с товарами
        """
        return Category.objects.filter(
            is_active=True,
            products__is_active=True
        ).distinct().order_by('order', 'name')
    
    @staticmethod
    def search_categories(query):
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
    
    @staticmethod
    def get_category_hierarchy(category):
        """
        Получает иерархию категории (от корня до текущей).
        
        Args:
            category: Категория
            
        Returns:
            list: Список категорий от корня до текущей
        """
        hierarchy = []
        current = category
        
        while current:
            hierarchy.insert(0, current)
            current = current.parent
        
        return hierarchy
    
    @staticmethod
    def get_category_tree():
        """
        Получает полное дерево категорий.
        
        Returns:
            QuerySet: Все категории для построения дерева
        """
        return Category.objects.filter(
            is_active=True
        ).select_related('parent').order_by('order', 'name')
    
    @staticmethod
    def get_popular_categories(limit=10):
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
            product_count=Count(
                'products',
                filter=Q(products__is_active=True)
            )
        ).filter(
            product_count__gt=0
        ).order_by('-product_count')[:limit]
    
    @staticmethod
    def get_categories_by_level(level=0):
        """
        Получает категории по уровню вложенности.
        
        Args:
            level: Уровень (0 - корневые, 1 - первый уровень и т.д.)
            
        Returns:
            QuerySet: Категории указанного уровня
        """
        queryset = Category.objects.filter(is_active=True)
        
        if level == 0:
            # Корневые категории
            queryset = queryset.filter(parent__isnull=True)
        elif level == 1:
            # Первый уровень вложенности
            queryset = queryset.filter(
                parent__isnull=False,
                parent__parent__isnull=True
            )
        elif level == 2:
            # Второй уровень вложенности
            queryset = queryset.filter(
                parent__isnull=False,
                parent__parent__isnull=False,
                parent__parent__parent__isnull=True
            )
        
        return queryset.order_by('order', 'name')
    
    @staticmethod
    def get_category_descendants(category):
        """
        Получает всех потомков категории.
        
        Args:
            category: Родительская категория
            
        Returns:
            QuerySet: Все потомки категории
        """
        # Получаем прямых потомков
        direct_children = Category.objects.filter(
            parent=category,
            is_active=True
        )
        
        # Рекурсивно получаем всех потомков
        all_descendants = list(direct_children)
        
        for child in direct_children:
            all_descendants.extend(
                CategoryRepository.get_category_descendants(child)
            )
        
        return all_descendants
    
    @staticmethod
    def get_category_tree_with_products():
        """
        Получение дерева категорий с продуктами.
        
        Returns:
            QuerySet: Дерево категорий с предзагруженными продуктами
        """
        return Category.objects.prefetch_related(
            'products',
            'children__products'
        ).filter(parent__isnull=True)
    
    @staticmethod
    def bulk_process_categories(chunk_size=1000):
        """
        Обработка категорий по частям для экономии памяти.
        
        Args:
            chunk_size: Размер чанка для обработки
            
        Yields:
            Category: Категории по одной
        """
        queryset = Category.objects.all().select_related('parent').order_by('id')
        
        # Используем iterator() для экономии памяти
        for category in queryset.iterator(chunk_size=chunk_size):
            yield category
    
    @staticmethod
    def bulk_process_categories_with_products(chunk_size=500):
        """
        Обработка категорий с продуктами по частям.
        
        Args:
            chunk_size: Размер чанка для обработки
            
        Yields:
            Category: Категории с предзагруженными продуктами
        """
        queryset = Category.objects.all().select_related('parent').prefetch_related(
            'products'
        ).order_by('id')
        
        for category in queryset.iterator(chunk_size=chunk_size):
            yield category
    
    @staticmethod
    def bulk_update_categories_in_chunks(updates_data, chunk_size=500):
        """
        Массовое обновление категорий по частям.
        
        Args:
            updates_data: Список кортежей (category_id, update_fields)
            chunk_size: Размер чанка для обновления
        """
        from django.db import transaction
        
        # Разбиваем на чанки
        for i in range(0, len(updates_data), chunk_size):
            chunk = updates_data[i:i + chunk_size]
            
            with transaction.atomic():
                categories_to_update = []
                category_ids = [item[0] for item in chunk]
                
                # Получаем категории для обновления
                categories = Category.objects.filter(id__in=category_ids)
                
                for category in categories:
                    # Находим соответствующие данные для обновления
                    for category_id, update_fields in chunk:
                        if category.id == category_id:
                            for field, value in update_fields.items():
                                setattr(category, field, value)
                            categories_to_update.append(category)
                            break
                
                # Массовое обновление
                if categories_to_update:
                    Category.objects.bulk_update(
                        categories_to_update, 
                        list(update_fields.keys())
                    )
    
    @staticmethod
    def get_categories_for_export(chunk_size=2000):
        """
        Получение категорий для экспорта с минимальным использованием памяти.
        
        Args:
            chunk_size: Размер чанка для обработки
            
        Yields:
            Category: Категории для экспорта
        """
        queryset = Category.objects.all().select_related(
            'parent'
        ).order_by('id')
        
        # Используем iterator для больших объемов данных
        for category in queryset.iterator(chunk_size=chunk_size):
            yield category