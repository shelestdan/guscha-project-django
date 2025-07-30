# -*- coding: utf-8 -*-
"""
Сервис для работы с изображениями товаров.

Этот модуль содержит бизнес-логику для управления изображениями товаров.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from ..models import Product, ProductImage
from ..validators.image_validator import ImageValidator
from ..utils.image_utils import ImageProcessor
import logging

logger = logging.getLogger(__name__)


class ImageService:
    """
    Сервис для работы с изображениями товаров.
    
    Предоставляет методы для загрузки, управления и обработки изображений.
    """
    
    def __init__(self):
        self.validator = ImageValidator()
        self.processor = ImageProcessor()
    
    def upload_multiple_images(self, product_id, images, user=None):
        """
        Загружает несколько изображений для товара.
        
        Args:
            product_id: ID товара
            images: Список файлов изображений
            user: Пользователь, выполняющий операцию
            
        Returns:
            dict: Результат операции с информацией о загруженных изображениях
        """
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        
        uploaded_images = []
        errors = []
        
        with transaction.atomic():
            for i, image in enumerate(images):
                try:
                    # Валидация изображения
                    self.validator.validate_image_file(image)
                    
                    # Создание объекта изображения
                    product_image = ProductImage.objects.create(
                        product=product,
                        image=image,
                        alt_text=f'Изображение товара {product.name}',
                        sort_order=ProductImage.objects.filter(product=product).count() + 1
                    )
                    
                    uploaded_images.append({
                        'id': product_image.id,
                        'url': product_image.image.url if product_image.image else None,
                        'alt_text': product_image.alt_text
                    })
                    
                except ValidationError as e:
                    errors.append(f'Изображение {i+1}: {str(e)}')
                except Exception as e:
                    logger.error(f'Ошибка при загрузке изображения {i+1}: {e}')
                    errors.append(f'Изображение {i+1}: Ошибка при загрузке')
        
        return {
            'success': len(uploaded_images) > 0,
            'uploaded_images': uploaded_images,
            'errors': errors,
            'total_uploaded': len(uploaded_images),
            'total_errors': len(errors)
        }
    
    def get_product_images(self, product_id):
        """
        Получает все изображения товара.
        
        Args:
            product_id: ID товара
            
        Returns:
            list: Список изображений товара
        """
        try:
            product = Product.objects.get(id=product_id)
            images = ProductImage.objects.filter(product=product).order_by('sort_order')
            
            return [
                {
                    'id': img.id,
                    'url': img.image.url if img.image else img.image_url,
                    'alt_text': img.alt_text,
                    'sort_order': img.sort_order,
                    'is_primary': img.is_primary
                }
                for img in images
            ]
        except Product.DoesNotExist:
            return []
    
    def reorder_images(self, product_id, image_orders):
        """
        Изменяет порядок изображений товара.
        
        Args:
            product_id: ID товара
            image_orders: Список с новым порядком изображений [{id: 1, order: 1}, ...]
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            
            with transaction.atomic():
                for item in image_orders:
                    try:
                        image = ProductImage.objects.get(
                            id=item['id'], 
                            product=product
                        )
                        image.sort_order = item['order']
                        image.save()
                    except ProductImage.DoesNotExist:
                        continue
            
            return {
                'success': True,
                'message': 'Порядок изображений обновлен'
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            logger.error(f'Ошибка при изменении порядка изображений: {e}')
            return {
                'success': False,
                'error': 'Ошибка при обновлении порядка изображений'
            }
    
    def set_primary_image(self, product_id, image_id):
        """
        Устанавливает основное изображение товара.
        
        Args:
            product_id: ID товара
            image_id: ID изображения
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            
            with transaction.atomic():
                # Сбрасываем флаг is_primary у всех изображений товара
                ProductImage.objects.filter(product=product).update(is_primary=False)
                
                # Устанавливаем новое основное изображение
                try:
                    image = ProductImage.objects.get(id=image_id, product=product)
                    image.is_primary = True
                    image.save()
                    
                    return {
                        'success': True,
                        'message': 'Основное изображение установлено'
                    }
                except ProductImage.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Изображение не найдено'
                    }
                    
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except Exception as e:
            logger.error(f'Ошибка при установке основного изображения: {e}')
            return {
                'success': False,
                'error': 'Ошибка при установке основного изображения'
            }
    
    def delete_image(self, product_id, image_id):
        """
        Удаляет изображение товара.
        
        Args:
            product_id: ID товара
            image_id: ID изображения
            
        Returns:
            dict: Результат операции
        """
        try:
            product = Product.objects.get(id=product_id)
            image = ProductImage.objects.get(id=image_id, product=product)
            
            # Удаляем файл изображения
            if image.image:
                image.image.delete(save=False)
            
            # Удаляем запись из базы данных
            image.delete()
            
            return {
                'success': True,
                'message': 'Изображение удалено'
            }
            
        except Product.DoesNotExist:
            return {
                'success': False,
                'error': 'Товар не найден'
            }
        except ProductImage.DoesNotExist:
            return {
                'success': False,
                'error': 'Изображение не найдено'
            }
        except Exception as e:
            logger.error(f'Ошибка при удалении изображения: {e}')
            return {
                'success': False,
                'error': 'Ошибка при удалении изображения'
            }