from rest_framework import serializers
from .models import CartItem
from apps.products.serializers import (
    ProductSerializer, ProductSizeSerializer,
    PreorderListSerializer, PreorderSizeSerializer
)


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элементов корзины"""
    product_detail = ProductSerializer(source='product', read_only=True)
    product_size_detail = ProductSizeSerializer(source='product_size', read_only=True)
    preorder_detail = PreorderListSerializer(source='preorder', read_only=True)
    preorder_size_detail = PreorderSizeSerializer(source='preorder_size', read_only=True)
    total_price = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()
    item_image = serializers.SerializerMethodField()
    product_image_url = serializers.SerializerMethodField()
    preorder_image_url = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    preorder_name = serializers.SerializerMethodField()
    size_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_detail', 'product_size', 'product_size_detail',
                  'preorder', 'preorder_detail', 'preorder_size', 'preorder_size_detail',
                  'quantity', 'price', 'total_price', 'item_type', 'item_name', 'item_image',
                  'product_image_url', 'preorder_image_url', 'product_name', 'preorder_name',
                  'size_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'price', 'total_price', 'item_name', 'item_image', 
                           'product_image_url', 'preorder_image_url', 'product_name', 
                           'preorder_name', 'size_name', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        """Вычисление общей стоимости позиции"""
        return float(obj.price * obj.quantity)
    
    def get_item_name(self, obj):
        """Получение названия товара или предзаказа"""
        if obj.item_type == 'product' and obj.product:
            return obj.product.name
        elif obj.item_type == 'preorder' and obj.preorder:
            return obj.preorder.name
        return "Неизвестный товар"
    
    def get_item_image(self, obj):
        """Получение изображения товара или предзаказа"""
        request = self.context.get('request')
        if obj.item_type == 'product' and obj.product:
            # Получаем изображение товара из image_url или primary_image
            image_url = None
            if obj.product.image_url:
                image_url = obj.product.image_url
            elif obj.product.primary_image:
                image_url = obj.product.primary_image.image_url
            
            if image_url and request:
                # Если URL уже абсолютный (начинается с http), возвращаем как есть
                if image_url.startswith('http'):
                    return image_url
                # Иначе строим абсолютный URL
                return request.build_absolute_uri(image_url)
            return image_url
        elif obj.item_type == 'preorder' and obj.preorder and obj.preorder.image_url:
            if request:
                # Если URL уже абсолютный (начинается с http), возвращаем как есть
                if obj.preorder.image_url.startswith('http'):
                    return obj.preorder.image_url
                # Иначе строим абсолютный URL
                return request.build_absolute_uri(obj.preorder.image_url)
            return obj.preorder.image_url
        return None
    
    def get_product_image_url(self, obj):
        """Получение URL изображения товара"""
        if obj.item_type == 'product' and obj.product:
            if obj.product.image_url:
                return obj.product.image_url
            elif obj.product.primary_image:
                return obj.product.primary_image.image_url
        return None
    
    def get_preorder_image_url(self, obj):
        """Получение URL изображения предзаказа"""
        if obj.item_type == 'preorder' and obj.preorder:
            return obj.preorder.image_url
        return None
    
    def get_product_name(self, obj):
        """Получение названия товара"""
        if obj.item_type == 'product' and obj.product:
            return obj.product.name
        return None
    
    def get_preorder_name(self, obj):
        """Получение названия предзаказа"""
        if obj.item_type == 'preorder' and obj.preorder:
            return obj.preorder.name
        return None
    
    def get_size_name(self, obj):
        """Получение названия размера"""
        if obj.item_type == 'product' and obj.product_size:
            return obj.product_size.size_name
        elif obj.item_type == 'preorder' and obj.preorder_size:
            return obj.preorder_size.size_name
        return None
