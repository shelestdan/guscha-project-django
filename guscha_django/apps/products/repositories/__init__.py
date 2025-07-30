# -*- coding: utf-8 -*-
"""
Репозитории для работы с данными товаров.

Этот модуль содержит классы для доступа к данным.
"""

from .product_repository import ProductRepository
from .category_repository import CategoryRepository

__all__ = [
    'ProductRepository',
    'CategoryRepository',
]