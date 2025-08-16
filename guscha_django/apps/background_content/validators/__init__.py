# -*- coding: utf-8 -*-
"""
Валидаторы для модуля background_content.
"""

from .image_validator import BackgroundImageValidator

# Создаем экземпляр валидатора для использования в моделях
background_image_validator = BackgroundImageValidator()

__all__ = ['BackgroundImageValidator', 'background_image_validator']