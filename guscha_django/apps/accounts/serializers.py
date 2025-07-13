from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'address')
        read_only_fields = ('id',)


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'address', 'password', 'password_confirm')
        read_only_fields = ('id',)
    
    def validate(self, attrs):
        # Проверяем, что пароли совпадают
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": _('Пароли не совпадают')})
        return attrs
    
    def create(self, validated_data):
        # Удаляем поле password_confirm, так как оно не нужно для создания пользователя
        validated_data.pop('password_confirm', None)
        
        # Создаем пользователя
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            address=validated_data.get('address', '')
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления данных пользователя"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'address')


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля"""
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        # Проверяем, что новые пароли совпадают
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": _('Новые пароли не совпадают')})
        return attrs


class LoginSerializer(serializers.Serializer):
    """Сериализатор для аутентификации пользователя"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            
            if not user:
                msg = _('Не удалось войти с предоставленными учетными данными.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Должны быть указаны "email" и "password".')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs