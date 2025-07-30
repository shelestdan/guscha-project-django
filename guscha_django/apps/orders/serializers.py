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
        """Создание заказа с элементами из корзины"""
        from apps.addresses.models import Address
        from apps.cart.models import CartItem
        from apps.cart.services import ReservationService
        from django.db import transaction
        
        billing_address_id = validated_data.pop('billing_address_id', None)
        shipping_address_id = validated_data.pop('shipping_address_id', None)
        
        user = self.context['request'].user
        request = self.context['request']
        
        with transaction.atomic():
            # Получаем товары из корзины пользователя
            cart_items = CartItem.objects.filter(user=user)
            
            if not cart_items.exists():
                raise serializers.ValidationError("Корзина пуста")
            
            # Используем существующие резервирования или создаем новые
            reservations = []
            for cart_item in cart_items:
                reservation = cart_item.reservation
                
                # Если резервирование уже существует, проверяем его актуальность
                if reservation and not reservation.is_expired():
                    # Проверяем, что количество в резервировании соответствует количеству в корзине
                    if reservation.quantity != cart_item.quantity:
                        # Обновляем количество в резервировании
                        success = ReservationService.update_reservation_quantity(
                            reservation.id, cart_item.quantity
                        )
                        if not success:
                            raise serializers.ValidationError(
                                f"Не удалось обновить резервирование для товара: {cart_item.product.name if cart_item.product else cart_item.preorder.name}"
                            )
                        # Обновляем объект резервирования
                        reservation.refresh_from_db()
                else:
                    # Создаем новое резервирование
                    if cart_item.item_type == 'product':
                        reservation = ReservationService.create_reservation(
                            user=user if user.is_authenticated else None,
                            session_id=request.headers.get('X-Session-ID') if not user.is_authenticated else None,
                            product=cart_item.product,
                            product_size=cart_item.product_size,
                            quantity=cart_item.quantity
                        )
                    elif cart_item.item_type == 'preorder':
                        reservation = ReservationService.create_reservation(
                            user=user if user.is_authenticated else None,
                            session_id=request.headers.get('X-Session-ID') if not user.is_authenticated else None,
                            preorder=cart_item.preorder,
                            preorder_size=cart_item.preorder_size,
                            quantity=cart_item.quantity
                        )
                    
                    if not reservation:
                        raise serializers.ValidationError(
                            f"Не удалось зарезервировать товар: {cart_item.product.name if cart_item.product else cart_item.preorder.name}. Возможно, недостаточно товара на складе."
                        )
                    
                    # Связываем резервирование с элементом корзины
                    cart_item.reservation = reservation
                    cart_item.save()
                
                reservations.append((cart_item, reservation))
            
            # Создаем заказ
            order = Order.objects.create(user=user, **validated_data)
            
            # Устанавливаем адреса
            if billing_address_id:
                order.billing_address_obj = Address.objects.get(id=billing_address_id)
            if shipping_address_id:
                order.shipping_address_obj = Address.objects.get(id=shipping_address_id)
            
            # Создаем элементы заказа из корзины с резервированиями
            for cart_item, reservation in reservations:
                # Создаем элемент заказа
                order_item = OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_size=cart_item.product_size,
                    preorder=cart_item.preorder,
                    preorder_size=cart_item.preorder_size,
                    name=cart_item.product.name if cart_item.product else cart_item.preorder.name,
                    size=cart_item.product_size.size if cart_item.product_size else (cart_item.preorder_size.size if cart_item.preorder_size else None),
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    item_type=cart_item.item_type,
                    reservation=reservation
                )
            
            # Очищаем корзину после создания заказа
            cart_items.delete()
            
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