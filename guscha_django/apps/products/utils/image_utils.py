# -*- coding: utf-8 -*-
"""
Утилиты для работы с изображениями товаров.

Этот модуль содержит вспомогательные функции для обработки изображений.
"""

import os
import uuid
from django.utils.text import slugify
from datetime import datetime


class ImageProcessor:
    """
    Процессор для работы с изображениями товаров.
    
    Предоставляет методы для генерации путей загрузки и обработки изображений.
    """
    
    def generate_upload_path(self, instance, filename):
        """
        Генерирует путь для загрузки изображения.
        
        Args:
            instance: Экземпляр модели
            filename: Имя файла
            
        Returns:
            str: Путь для загрузки файла
        """
        # Получаем расширение файла
        ext = filename.split('.')[-1].lower()
        
        # Генерируем уникальное имя файла
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Определяем тип модели для создания соответствующей папки
        if hasattr(instance, 'product'):
            # Это изображение товара
            if hasattr(instance.product, 'slug'):
                product_slug = slugify(instance.product.slug)
            else:
                product_slug = 'product'
            return f'products/{product_slug}/images/{unique_filename}'
        elif hasattr(instance, 'slug'):
            # Это сам товар или предзаказ
            model_slug = slugify(instance.slug)
            model_type = instance.__class__.__name__.lower()
            return f'{model_type}s/{model_slug}/images/{unique_filename}'
        else:
            # Общий случай
            year = datetime.now().year
            month = datetime.now().month
            return f'uploads/{year}/{month:02d}/{unique_filename}'
    
    def get_image_dimensions(self, image_path):
        """
        Получает размеры изображения.
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            tuple: (ширина, высота) или (None, None) при ошибке
        """
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return (None, None)
    
    def optimize_image(self, image_path, max_width=1920, max_height=1080, quality=85):
        """
        Оптимизирует изображение для веб-использования.
        
        Args:
            image_path: Путь к изображению
            max_width: Максимальная ширина
            max_height: Максимальная высота
            quality: Качество сжатия (1-100)
            
        Returns:
            bool: True если оптимизация прошла успешно
        """
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                # Конвертируем в RGB если необходимо
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Изменяем размер если необходимо
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Сохраняем с оптимизацией
                img.save(image_path, optimize=True, quality=quality)
                return True
        except Exception:
            return False


# Функции для обратной совместимости
def product_image_upload_path(instance, filename):
    """
    Функция для генерации пути загрузки изображений товаров.
    Используется в моделях для поля upload_to.
    """
    processor = ImageProcessor()
    return processor.generate_upload_path(instance, filename)


def preorder_image_upload_path(instance, filename):
    """
    Функция для генерации пути загрузки изображений предзаказов.
    Используется в моделях для поля upload_to.
    """
    processor = ImageProcessor()
    return processor.generate_upload_path(instance, filename)