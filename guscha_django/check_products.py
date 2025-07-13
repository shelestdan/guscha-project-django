#!/usr/bin/env python
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_project.settings')
django.setup()

from apps.products.models import Product
from apps.products.serializers import ProductListSerializer

print("=== ПРОВЕРКА ТОВАРОВ В БАЗЕ ДАННЫХ ===")
print(f"Общее количество товаров: {Product.objects.count()}")
print(f"Активных товаров: {Product.objects.filter(is_active=True).count()}")

print("\n=== ПЕРВЫЕ 5 ТОВАРОВ ===")
products = Product.objects.all()[:5]
for product in products:
    print(f"ID: {product.id}")
    print(f"Название: {product.name}")
    print(f"Активен: {product.is_active}")
    print(f"Цена: {product.price}")
    print(f"Категория: {product.category}")
    print("-" * 40)

print("\n=== ПРОВЕРКА API СЕРИАЛИЗАЦИИ ===")
active_products = Product.objects.filter(is_active=True)[:3]
if active_products:
    serializer = ProductListSerializer(active_products, many=True)
    print("Сериализованные данные:")
    import json
    print(json.dumps(serializer.data, indent=2, ensure_ascii=False))
else:
    print("Нет активных товаров для сериализации")