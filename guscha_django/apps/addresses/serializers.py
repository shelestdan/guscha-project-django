from rest_framework import serializers
from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Address"""
    
    full_address = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'first_name', 'last_name', 'company',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'phone', 'is_default', 'is_active', 'full_address',
            'full_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_address', 'full_name']
    
    def validate(self, data):
        """Валидация данных адреса"""
        # Проверяем обязательные поля
        required_fields = ['first_name', 'last_name', 'address_line1', 'city', 'postal_code']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: f'{field} обязателен для заполнения'})
        
        # Проверяем уникальность адреса по умолчанию
        if data.get('is_default', False):
            user = self.context['request'].user
            address_type = data.get('address_type', 'shipping')
            
            existing_default = Address.objects.filter(
                user=user,
                address_type=address_type,
                is_default=True
            ).exclude(id=getattr(self.instance, 'id', None))
            
            if existing_default.exists():
                raise serializers.ValidationError({
                    'is_default': 'У вас уже есть адрес по умолчанию для этого типа'
                })
        
        return data
    
    def create(self, validated_data):
        """Создание нового адреса"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания адреса"""
    
    class Meta:
        model = Address
        fields = [
            'address_type', 'first_name', 'last_name', 'company',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'phone', 'is_default'
        ]
    
    def validate(self, data):
        """Валидация при создании"""
        return super().validate(data)


class AddressUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления адреса"""
    
    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'company', 'address_line1', 
            'address_line2', 'city', 'state', 'postal_code', 'country', 
            'phone', 'is_default'
        ]
    
    def validate_is_default(self, value):
        """Валидация поля is_default"""
        if value:
            user = self.context['request'].user
            address_type = self.instance.address_type
            
            existing_default = Address.objects.filter(
                user=user,
                address_type=address_type,
                is_default=True
            ).exclude(id=self.instance.id)
            
            if existing_default.exists():
                raise serializers.ValidationError(
                    'У вас уже есть адрес по умолчанию для этого типа'
                )
        
        return value


class AddressListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка адресов"""
    
    full_address = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'full_name', 'full_address', 
            'is_default', 'is_active', 'created_at'
        ]