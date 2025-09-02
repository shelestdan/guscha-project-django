# -*- coding: utf-8 -*-
"""
Валидаторы изображений для товаров.

Этот модуль содержит валидаторы для проверки изображений товаров.
"""

from django.core.exceptions import ValidationError
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageValidator:
    """
    Валидатор для изображений товаров.
    
    Проверяет размер файла, формат и размеры изображения.
    """
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.min_width = 100
        self.min_height = 100
        self.allowed_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']
    
    def validate_image_file(self, image):
        """
        Валидация файла изображения.
        
        Args:
            image: Файл изображения для валидации
            
        Raises:
            ValidationError: Если изображение не прошло валидацию
        """
        if not image:
            return
            
        # Проверка размера файла
        if image.size > self.max_file_size:
            raise ValidationError(
                f'Размер файла не должен превышать {self.max_file_size // (1024 * 1024)}MB. '
                f'Текущий размер: {image.size // (1024 * 1024)}MB'
            )
        
        try:
            # Открываем изображение для проверки формата и размеров
            with Image.open(image) as img:
                # Проверка формата
                if img.format not in self.allowed_formats:
                    raise ValidationError(
                        f'Неподдерживаемый формат изображения: {img.format}. '
                        f'Поддерживаемые форматы: {", ".join(self.allowed_formats)}'
                    )
                
                # Проверка минимальных размеров
                width, height = img.size
                if width < self.min_width or height < self.min_height:
                    raise ValidationError(
                        f'Минимальный размер изображения: {self.min_width}x{self.min_height}px. '
                        f'Текущий размер: {width}x{height}px'
                    )
                    
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.error(f'Ошибка при валидации изображения: {e}')
            raise ValidationError('Не удалось обработать изображение. Проверьте, что файл не поврежден.')
        
        # Сбрасываем указатель файла в начало после чтения
        image.seek(0)