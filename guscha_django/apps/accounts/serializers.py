from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Импорты утилит и валидаторов
from .utils import ValidationUtils, SecurityUtils
from .models import PendingUserRegistration

User = get_user_model()


class BaseSerializer(serializers.Serializer):
    """Базовый сериализатор с общими методами"""
    
    def validate_email(self, value):
        """Валидация email адреса"""
        validation_result = ValidationUtils.validate_email(value)
        if not validation_result['is_valid']:
            raise serializers.ValidationError(
                validation_result['error']
            )
        return validation_result.get('normalized_email', value.lower().strip())
    
    def validate_phone(self, value):
        """Валидация номера телефона"""
        if value:
            result = ValidationUtils.validate_phone_number(value)
            if not result['is_valid']:
                raise serializers.ValidationError(
                    result.get('error', 'Введите корректный номер телефона')
                )
        return value
    
    def validate_password(self, value):
        """Валидация пароля"""
        validation_result = SecurityUtils.validate_password_strength(value)
        if not validation_result['is_valid']:
            raise serializers.ValidationError(
                validation_result['errors']
            )
        return value
    
    def validate_name(self, value, field_name='name'):
        """Валидация имени"""
        if value:
            result = ValidationUtils.validate_name(value)
            if not result:
                raise serializers.ValidationError(f"Поле {field_name} содержит недопустимые символы")
        
        return value.strip().title() if value else value


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя"""
    
    full_name = serializers.SerializerMethodField()
    is_telegram_linked = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'address', 'date_joined', 'last_login',
            'is_active', 'is_telegram_verified', 'is_telegram_linked',
            'account_status', 'last_activity'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'is_telegram_verified',
            'full_name', 'is_telegram_linked', 'account_status', 'last_activity'
        ]
    
    def get_full_name(self, obj) -> str:
        """Получение полного имени"""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_is_telegram_linked(self, obj) -> bool:
        """Проверка привязки Telegram"""
        return bool(obj.telegram_chat_id and obj.is_telegram_verified)
    
    def get_account_status(self, obj) -> str:
        """Получение статуса аккаунта"""
        if not obj.is_active:
            return 'inactive'
        elif obj.is_telegram_verified:
            return 'verified'
        else:
            return 'pending_verification'
    
    def get_last_activity(self, obj) -> str:
        """Получение времени последней активности"""
        return obj.last_login.isoformat() if obj.last_login else None


class UserCreateSerializer(BaseSerializer, serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Пароль должен содержать минимум 8 символов'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Подтверждение пароля'
    )
    terms_accepted = serializers.BooleanField(
        write_only=True,
        help_text='Согласие с условиями использования'
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone', 'address',
            'password', 'password_confirm', 'terms_accepted'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'address': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def validate_first_name(self, value):
        """Валидация имени"""
        return self.validate_name(value, 'имя')
    
    def validate_last_name(self, value):
        """Валидация фамилии"""
        return self.validate_name(value, 'фамилия')
    
    def validate_phone(self, value):
        """Валидация телефона с проверкой уникальности"""
        if not value:
            return value
            
        # Базовая валидация
        value = super().validate_phone(value)
        
        # Проверка существующего активного пользователя с таким телефоном
        existing_user = User.objects.filter(phone=value).first()
        if existing_user:
            if existing_user.is_active and existing_user.is_telegram_verified:
                raise serializers.ValidationError(
                    'Пользователь с таким номером телефона уже существует'
                )
            elif not existing_user.is_telegram_verified:
                # Если пользователь существует, но не подтвержден через Telegram,
                # удаляем его для повторной регистрации
                logger.info(f"Удаление неподтвержденного пользователя с телефоном {existing_user.phone} для повторной регистрации")
                existing_user.delete()
        
        return value
    
    def validate_email(self, value):
        """Валидация email с проверкой уникальности"""
        value = super().validate_email(value)
        
        # Проверка существующего активного пользователя
        existing_user = User.objects.filter(email=value).first()
        if existing_user:
            if existing_user.is_active and existing_user.is_telegram_verified:
                raise serializers.ValidationError(
                    'Пользователь с таким email уже существует'
                )
            elif not existing_user.is_telegram_verified:
                # Если пользователь существует, но не подтвержден через Telegram,
                # удаляем его для повторной регистрации
                logger.info(f"Удаление неподтвержденного пользователя {existing_user.email} для повторной регистрации")
                existing_user.delete()
        
        # Проверка в pending регистрациях (удаляем старые)
        PendingUserRegistration.objects.filter(
            email=value,
            expires_at__lt=timezone.now()
        ).delete()
        
        # Проверка активных pending регистраций
        active_pending = PendingUserRegistration.objects.filter(
            email=value,
            expires_at__gt=timezone.now()
        ).first()
        
        if active_pending:
            # Если прошло более 5 минут, позволяем создать новую
            if timezone.now() - active_pending.created_at > timezone.timedelta(minutes=5):
                active_pending.delete()
            else:
                # Сохраняем информацию о существующей регистрации в контексте
                self.context['existing_pending_id'] = active_pending.id
                # Не выбрасываем ошибку, а продолжаем валидацию
        
        return value
    
    def validate_terms_accepted(self, value):
        """Валидация согласия с условиями"""
        if not value:
            raise serializers.ValidationError(
                'Необходимо принять условия использования'
            )
        return value
    
    def validate(self, attrs):
        """Общая валидация данных"""
        # Проверка совпадения паролей
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Пароли не совпадают'
            })
        
        # Проверка пароля на основе других данных
        email = attrs.get('email', '')
        first_name = attrs.get('first_name', '')
        last_name = attrs.get('last_name', '')
        
        if ValidationUtils.password_contains_personal_info(
            password, email, first_name, last_name
        ):
            raise serializers.ValidationError({
                'password': 'Пароль не должен содержать личную информацию'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Создание pending регистрации"""
        # Удаляем поля, которые не нужны для модели
        validated_data.pop('password_confirm', None)
        validated_data.pop('terms_accepted', None)
        
        # Удаляем предыдущие незавершённые pending регистрации для этого email
        PendingUserRegistration.objects.filter(email=validated_data['email']).delete()
        
        # Создаем pending регистрацию
        from django.contrib.auth.hashers import make_password
        
        password = validated_data.pop('password')
        pending_registration = PendingUserRegistration.objects.create(
            **validated_data,
            password_hash=make_password(password)
        )
        
        # Возвращаем объект с ID pending регистрации для дальнейшего использования
        user_data = validated_data.copy()
        user_data['pending_registration_id'] = pending_registration.id
        
        return type('PendingUser', (), user_data)


class UserUpdateSerializer(BaseSerializer, serializers.ModelSerializer):
    """Сериализатор для обновления пользователя"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address']
    
    def validate_first_name(self, value):
        """Валидация имени"""
        return self.validate_name(value, 'имя')
    
    def validate_last_name(self, value):
        """Валидация фамилии"""
        return self.validate_name(value, 'фамилия')
    
    def validate(self, attrs):
        """Общая валидация обновления"""
        # Проверяем, что хотя бы одно поле изменяется
        if not any(attrs.values()):
            raise serializers.ValidationError(
                'Необходимо указать хотя бы одно поле для обновления'
            )
        
        return attrs


class ChangePasswordSerializer(BaseSerializer):
    """Сериализатор для изменения пароля"""
    
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Валидация нового пароля"""
        return self.validate_password(value)
    
    def validate(self, attrs):
        """Общая валидация смены пароля"""
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Проверка совпадения новых паролей
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'Пароли не совпадают'
            })
        
        # Проверка, что новый пароль отличается от старого
        if old_password == new_password:
            raise serializers.ValidationError({
                'new_password': 'Новый пароль должен отличаться от текущего'
            })
        
        return attrs


class LoginSerializer(BaseSerializer):
    """Сериализатор для аутентификации"""
    
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    remember_me = serializers.BooleanField(
        default=False,
        required=False
    )
    
    def validate_email(self, value):
        """Валидация email"""
        return super().validate_email(value)
    
    def validate(self, attrs):
        """Валидация аутентификации"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError(
                'Email и пароль обязательны для заполнения'
            )
        
        # Проверяем существование пользователя
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Неверный email или пароль'
            )
        
        # Проверяем активность аккаунта
        if not user.is_active:
            raise serializers.ValidationError(
                'Аккаунт деактивирован'
            )
        
        # Аутентификация
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        
        if not user:
            raise serializers.ValidationError(
                'Неверный email или пароль'
            )
        
        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(BaseSerializer):
    """Сериализатор для запроса сброса пароля"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Валидация email"""
        return super().validate_email(value)
    
    def save(self):
        """Инициация сброса пароля"""
        email = self.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # Здесь будет вызван сервис для отправки email
            logger.info(f'Password reset requested for user: {user.email}')
        except User.DoesNotExist:
            # Не раскрываем информацию о существовании пользователя
            logger.info(f'Password reset requested for non-existent email: {email}')
        
        return email


class PasswordResetConfirmSerializer(BaseSerializer):
    """Сериализатор для подтверждения сброса пароля"""
    
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Валидация нового пароля"""
        return self.validate_password(value)
    
    def validate(self, attrs):
        """Валидация данных сброса пароля"""
        uid = attrs.get('uid')
        token = attrs.get('token')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')
        
        # Проверка совпадения паролей
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': 'Пароли не совпадают'
            })
        
        # Проверка токена
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({
                'uid': 'Неверная ссылка для сброса пароля'
            })
        
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({
                'token': 'Неверный или истекший токен'
            })
        
        attrs['user'] = user
        return attrs
    
    def save(self):
        """Сохранение нового пароля"""
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        
        user.set_password(new_password)
        user.save()
        
        logger.info(f'Password reset completed for user: {user.email}')
        return user


class TelegramVerificationSerializer(serializers.Serializer):
    """Сериализатор для верификации через Telegram"""
    
    verification_code = serializers.CharField(
        max_length=6,
        min_length=6,
        help_text='6-значный код верификации'
    )
    telegram_username = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Telegram username (опционально)'
    )
    
    def validate_verification_code(self, value):
        """Валидация кода верификации"""
        if not value.isdigit():
            raise serializers.ValidationError(
                'Код верификации должен содержать только цифры'
            )
        return value
    
    def validate_telegram_username(self, value):
        """Валидация Telegram username"""
        if value and not ValidationUtils.validate_telegram_username(value):
            raise serializers.ValidationError(
                'Неверный формат Telegram username'
            )
        return value


class QRCodeCreateSerializer(serializers.Serializer):
    """Сериализатор для создания QR кода"""
    
    type = serializers.ChoiceField(
        choices=['registration', 'login', 'verification'],
        default='registration',
        help_text='Тип QR кода'
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text='Описание QR кода'
    )
    user_data = serializers.JSONField(
        required=False,
        help_text='Данные пользователя для регистрации'
    )
    
    def validate_user_data(self, value):
        """Валидация данных пользователя"""
        if not value:
            return value
        
        # Проверяем обязательные поля для регистрации
        required_fields = ['email', 'first_name', 'last_name']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f'Поле {field} обязательно для регистрации'
                )
        
        # Валидируем email
        email = value.get('email')
        if email:
            validation_result = ValidationUtils.validate_email(email)
            if not validation_result['is_valid']:
                raise serializers.ValidationError(
                    validation_result['error']
                )
        
        return value


class UserStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики пользователя"""
    
    total_logins = serializers.IntegerField(read_only=True)
    last_login_ip = serializers.CharField(read_only=True)
    telegram_verifications = serializers.IntegerField(read_only=True)
    qr_scans = serializers.IntegerField(read_only=True)
    account_age_days = serializers.IntegerField(read_only=True)
    security_events = serializers.IntegerField(read_only=True)
    
    class Meta:
        fields = [
            'total_logins', 'last_login_ip', 'telegram_verifications',
            'qr_scans', 'account_age_days', 'security_events'
        ]


class TelegramLinkSerializer(serializers.Serializer):
    """Сериализатор для привязки Telegram аккаунта"""
    
    telegram_username = serializers.CharField(
        max_length=32,
        help_text='Telegram username без @'
    )
    telegram_chat_id = serializers.CharField(
        help_text='Telegram Chat ID'
    )
    
    def validate_telegram_username(self, value):
        """Валидация Telegram username"""
        if not ValidationUtils.validate_telegram_username(value):
            raise serializers.ValidationError(
                'Неверный формат Telegram username'
            )
        return value
    
    def validate_telegram_chat_id(self, value):
        """Валидация Telegram Chat ID"""
        try:
            int(value)
        except ValueError:
            raise serializers.ValidationError(
                'Telegram Chat ID должен быть числом'
            )
        return value


class SecurityEventSerializer(serializers.Serializer):
    """Сериализатор для событий безопасности"""
    
    event_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    details = serializers.JSONField(read_only=True)
    severity = serializers.CharField(read_only=True)
    
    class Meta:
        fields = [
            'event_type', 'timestamp', 'ip_address',
            'user_agent', 'details', 'severity'
        ]