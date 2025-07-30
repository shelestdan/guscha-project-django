# -*- coding: utf-8 -*-
"""
Сервис для работы с товарами.

Этот модуль содержит бизнес-логику для управления товарами.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from ..models import Product, ProductReview, Wishlist, ProductImage
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ProductService:
    """
    Сервис для работы с товарами.
    
    Предоставляет методы для управления товарами, отзывами и списком желаний.
    """
    
    def get_optimized_queryset(self, filters=None):
        """
        Получает оптимизированный queryset товаров с фильтрацией.
        
        Args:
            filters: Словарь с фильтрами
            
        Returns:
            QuerySet: Оптимизированный queryset товаров
        """
        queryset = Product.objects.select_related(
            'category'
        ).prefetch_related(
            'product_images',
            'sizes',
            'reviews'
        ).filter(is_active=True)
        
        if filters:
            # Применяем фильтры
            if 'category' in filters:
                queryset = queryset.filter(category=filters['category'])
            
            if 'price_min' in filters:
                queryset = queryset.filter(price__gte=filters['price_min'])
            
            if 'price_max' in filters:
                queryset = queryset.filter(price__lte=filters['price_max'])
            
            if 'in_stock' in filters and filters['in_stock']:
                queryset = queryset.filter(stock_quantity__gt=0)
            
            if 'featured' in filters and filters['featured']:
                queryset = queryset.filter(is_featured=True)
        
        return queryset
    
    def add_review(self, product_id, user, rating, comment=None):
        """
        Добавляет отзыв к товару.
        
        Args:
            product_id: ID товара
            user: Пользователь
            rating: Оценка (1-5)
            comment: Комментарий
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Проверяем, не оставлял ли пользователь уже отзыв
            if ProductReview.objects.filter(product=product, user=user).exists():
                return {
                    'success': False,
                    'error': 'Вы уже оставили отзыв на этот товар'
                }
            
            # Создаем отзыв
            review = ProductReview.objects.create(
                product=product,
                user=user,
                rating=rating,
                comment=comment or ''
            )
            
            return {
                'success': True,
                'review': {
                    'id': review.id,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at,
                    'user': {
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                }
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except ValidationError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f'Ошибка при добавлении отзыва: {e}')
            return {
                'success': False,
                'error': 'Ошибка при добавлении отзыва'
            }
    
    def add_to_wishlist(self, product_id, user):
        """
        Добавляет товар в список желаний.
        
        Args:
            product_id: ID товара
            user: Пользователь
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            
            # Проверяем, нет ли товара уже в списке желаний
            wishlist_item, created = Wishlist.objects.get_or_create(
                product=product,
                user=user
            )
            
            if created:
                return {
                    'success': True,
                    'message': 'Товар добавлен в список желаний'
                }
            else:
                return {
                    'success': False,
                    'error': 'Товар уже в списке желаний'
                }
                
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            logger.error(f'Ошибка при добавлении в список желаний: {e}')
            return {
                'success': False,
                'error': 'Ошибка при добавлении в список желаний'
            }
    
    def remove_from_wishlist(self, product_id, user):
        """
        Удаляет товар из списка желаний.
        
        Args:
            product_id: ID товара
            user: Пользователь
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            
            deleted_count, _ = Wishlist.objects.filter(
                product=product,
                user=user
            ).delete()
            
            if deleted_count > 0:
                return {
                    'success': True,
                    'message': 'Товар удален из списка желаний'
                }
            else:
                return {
                    'success': False,
                    'error': 'Товар не найден в списке желаний'
                }
                
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            logger.error(f'Ошибка при удалении из списка желаний: {e}')
            return {
                'success': False,
                'error': 'Ошибка при удалении из списка желаний'
            }
    
    def post_save_processing(self, product, created=False):
        """
        Обработка после сохранения товара.
        
        Args:
            product: Экземпляр товара
            created: Флаг создания нового товара
            
        Returns:
            dict: Результат обработки
        """
        try:
            messages = []
            
            # Обновляем основное изображение если необходимо
            if not product.primary_image:
                first_image = ProductImage.objects.filter(product=product).first()
                if first_image:
                    first_image.is_primary = True
                    first_image.save()
                    messages.append('Установлено основное изображение')
            
            # Проверяем наличие размеров
            if not product.sizes.exists():
                messages.append('Внимание: У товара нет размеров')
            
            # Проверяем наличие изображений
            if not product.product_images.exists():
                messages.append('Внимание: У товара нет изображений')
            
            return {
                'success': True,
                'messages': messages
            }
            
        except Exception as e:
            logger.error(f'Ошибка при пост-обработке товара: {e}')
            return {
                'success': False,
                'error': 'Ошибка при обработке товара'
            }
    
    def update_stock(self, product_id, quantity_change):
        """
        Обновляет количество товара на складе.
        
        Args:
            product_id: ID товара
            quantity_change: Изменение количества (может быть отрицательным)
            
        Returns:
            dict: Результат операции
        """
        try:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(id=product_id)
                
                new_quantity = product.stock_quantity + quantity_change
                
                if new_quantity < 0:
                    return {
                        'success': False,
                        'error': 'Недостаточно товара на складе'
                    }
                
                product.stock_quantity = new_quantity
                product.save()
                
                return {
                    'success': True,
                    'new_quantity': new_quantity
                }
                
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            logger.error(f'Ошибка при обновлении количества товара: {e}')
            return {
                'success': False,
                'error': 'Ошибка при обновлении количества товара'
            }