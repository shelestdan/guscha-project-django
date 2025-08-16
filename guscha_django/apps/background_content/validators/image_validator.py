# -*- coding: utf-8 -*-
"""
Валидаторы изображений для фонового контента.

Этот модуль содержит валидаторы для проверки изображений фонового контента и слайдшоу.
"""

from django.core.exceptions import ValidationError
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class BackgroundImageValidator:
    """
    Валидатор для изображений фонового контента.
    
    Проверяет размер файла, формат и размеры изображения.
    Адаптирован для фоновых изображений и слайдшоу.
    """
    
    def __init__(self):
        self.max_file_size = 15 * 1024 * 1024  # 15MB для фоновых изображений
        self.min_width = 400  # Минимальная ширина для фоновых изображений (смягчено)
        self.min_height = 300  # Минимальная высота для фоновых изображений (смягчено)
        self.allowed_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']  # Добавлен JPG формат
        self.recommended_width = 1920
        self.recommended_height = 1080
    
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
                # Проверка формата (PIL может возвращать JPEG для JPG файлов)
                img_format = img.format
                if img_format == 'JPEG':
                    img_format = 'JPG'  # Нормализуем для совместимости
                
                if img_format not in self.allowed_formats and img.format not in self.allowed_formats:
                    raise ValidationError(
                        f'Неподдерживаемый формат изображения: {img.format}. '
                        f'Поддерживаемые форматы: JPG, JPEG, PNG, WebP'
                    )
                
                # Проверка минимальных размеров
                width, height = img.size
                if width < self.min_width or height < self.min_height:
                    raise ValidationError(
                        f'Минимальный размер изображения: {self.min_width}x{self.min_height}px. '
                        f'Текущий размер: {width}x{height}px'
                    )
                
                # Предупреждение о рекомендуемых размерах (не блокирующее)
                if width < self.recommended_width or height < self.recommended_height:
                    logger.warning(
                        f'Рекомендуемый размер изображения: {self.recommended_width}x{self.recommended_height}px. '
                        f'Текущий размер: {width}x{height}px'
                    )
                    
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.error(f'Ошибка при валидации изображения: {e}')
            raise ValidationError('Не удалось обработать изображение. Проверьте, что файл не поврежден.')
        
        # Сбрасываем указатель файла в начало после чтения
        image.seek(0)
    
    def validate_slideshow_image(self, image):
        """
        Специальная валидация для изображений слайдшоу.
        
        Args:
            image: Файл изображения для валидации
            
        Raises:
            ValidationError: Если изображение не прошло валидацию
        """
        # Используем базовую валидацию
        self.validate_image_file(image)
        
        # Дополнительные проверки для слайдшоу
        try:
            with Image.open(image) as img:
                width, height = img.size
                aspect_ratio = width / height
                
                # Проверяем соотношение сторон (рекомендуется 16:9 или близко к нему)
                recommended_ratio = 16 / 9
                if abs(aspect_ratio - recommended_ratio) > 0.5:
                    logger.warning(
                        f'Рекомендуемое соотношение сторон для слайдшоу: 16:9 ({recommended_ratio:.2f}). '
                        f'Текущее соотношение: {aspect_ratio:.2f}'
                    )
        except Exception as e:
            logger.error(f'Ошибка при дополнительной валидации слайдшоу: {e}')
        
        # Сбрасываем указатель файла в начало после чтения
        image.seek(0)