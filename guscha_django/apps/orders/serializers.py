from rest_framework import serializers
from .models import Order, OrderItem
from apps.addresses.serializers import AddressSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элемента заказа"""
    
    total = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'name', 'size', 'quantity', 'price', 'total', 'item_type'
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказа"""
    
    items = OrderItemSerializer(many=True, read_only=True)
    billing_address = AddressSerializer(read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'fulfillment_status',
            'subtotal', 'tax', 'shipping', 'discount', 'total', 'billing_address',
            'shipping_address', 'shipping_method', 'payment_method', 'tracking_number',
            'transaction_id', 'notes', 'created_at', 'updated_at', 'shipped_at',
            'delivered_at', 'items'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заказа"""
    
    billing_address_id = serializers.IntegerField(required=False)
    shipping_address_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Order
        fields = [
            'email', 'subtotal', 'tax', 'shipping', 'discount', 'total',
            'billing_address_id', 'shipping_address_id', 'shipping_method',
            'payment_method', 'notes'
        ]
    
    def validate_billing_address_id(self, value):
        """Валидация адреса оплаты"""
        if value:
            from apps.addresses.models import Address
            try:
                address = Address.objects.get(id=value, user=self.context['request'].user)
                if address.address_type != 'billing':
                    raise serializers.ValidationError('Адрес должен быть типа "billing"')
            except Address.DoesNotExist:
                raise serializers.ValidationError('Адрес не найден')
        return value
    
    def validate_shipping_address_id(self, value):
        """Валидация адреса доставки"""
        if value:
            from apps.addresses.models import Address
            try:
                address = Address.objects.get(id=value, user=self.context['request'].user)
                if address.address_type != 'shipping':
                    raise serializers.ValidationError('Адрес должен быть типа "shipping"')
            except Address.DoesNotExist:
                raise serializers.ValidationError('Адрес не найден')
        return value
    
    def create(self, validated_data):
        """Создание заказа"""
        billing_address_id = validated_data.pop('billing_address_id', None)
        shipping_address_id = validated_data.pop('shipping_address_id', None)
        
        order = Order.objects.create(**validated_data)
        
        if billing_address_id:
            from apps.addresses.models import Address
            order.billing_address = Address.objects.get(id=billing_address_id)
        
        if shipping_address_id:
            from apps.addresses.models import Address
            order.shipping_address = Address.objects.get(id=shipping_address_id)
        
        order.save()
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления заказа"""
    
    billing_address_id = serializers.IntegerField(required=False)
    shipping_address_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = Order
        fields = [
            'status', 'payment_status', 'fulfillment_status', 'shipping_method',
            'payment_method', 'tracking_number', 'transaction_id', 'notes',
            'billing_address_id', 'shipping_address_id'
        ]
    
    def update(self, instance, validated_data):
        """Обновление заказа"""
        billing_address_id = validated_data.pop('billing_address_id', None)
        shipping_address_id = validated_data.pop('shipping_address_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if billing_address_id is not None:
            from apps.addresses.models import Address
            if billing_address_id:
                instance.billing_address = Address.objects.get(id=billing_address_id)
            else:
                instance.billing_address = None
        
        if shipping_address_id is not None:
            from apps.addresses.models import Address
            if shipping_address_id:
                instance.shipping_address = Address.objects.get(id=shipping_address_id)
            else:
                instance.shipping_address = None
        
        instance.save()
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка заказов"""
    
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status', 'total',
            'created_at', 'items_count'
        ]
    
    def get_items_count(self, obj):
        """Получение количества товаров в заказе"""
        return obj.items.count()