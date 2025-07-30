# -*- coding: utf-8 -*-
"""
Администрирование приложения products.

Этот модуль содержит классы администрирования для товаров и предзаказов,
разделенные согласно принципам SOLID для лучшей поддерживаемости кода.
"""

from .category_admin import CategoryAdmin
from .product_admin import ProductAdmin, ProductSizeAdmin, ProductImageAdmin, ProductSizeInline, ProductImageInline
from .preorder_admin import PreorderAdmin, PreorderSizeAdmin, PreorderImageAdmin, PreorderSizeInline, PreorderImageInline

__all__ = [
    'CategoryAdmin',
    'ProductAdmin',
    'ProductSizeAdmin',
    'ProductImageAdmin',
    'ProductSizeInline', 
    'ProductImageInline',
    'PreorderAdmin',
    'PreorderSizeAdmin',
    'PreorderImageAdmin',
    'PreorderSizeInline',
    'PreorderImageInline'
]