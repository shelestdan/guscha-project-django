from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Импорты сервисов
from .services import UserService, AuthService, TelegramService, QRService
from .utils import SecurityUtils, ValidationUtils
from .models import TelegramVerificationCode, PendingUserRegistration, QRCodeScan
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()


class BaseViewMixin:
    """Базовый миксин для представлений с общими методами"""

    def get_client_info(self, request) -> Dict[str, Any]:
        """Получение информации о клиенте"""
        return {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request),
            'is_secure': SecurityUtils.is_secure_connection(request)
        }
    
    def check_security(self, request, identifier: str = None) -> Dict[str, Any]:
        """Проверка безопасности запроса"""
        print(f"DEBUG: check_security called with identifier='{identifier}'")
        client_info = self.get_client_info(request)
        ip_address = client_info['ip_address']
        print(f"DEBUG: client IP address: {ip_address}")
        
        # Проверка IP адреса
        if SecurityUtils.is_ip_blacklisted(ip_address):
            SecurityUtils.log_security_event(
                'blocked_ip_access',
                {'ip_address': ip_address},
                ip_address=ip_address
            )
            return {
                'allowed': False,
                'error': 'Доступ запрещен'
            }
        
        # Проверка rate limit
        if identifier:
            rate_limit = SecurityUtils.check_rate_limit(identifier)
            if not rate_limit['allowed']:
                SecurityUtils.log_security_event(
                    'rate_limit_exceeded',
                    {'identifier': identifier, 'ip_address': ip_address},
                    ip_address=ip_address
                )
                return {
                    'allowed': False,
                    'error': 'Превышен лимит запросов',
                    'retry_after': rate_limit.get('remaining_time_seconds', 0)
                }
        
        return {'allowed': True}
    
    def handle_error(self, error: Exception, request=None) -> Response:
        """Обработка ошибок"""
        logger.error(f'Error in {self.__class__.__name__}: {str(error)}')
        
        if isinstance(error, ValidationError):
            return Response(
                {'error': 'Ошибка валидации', 'details': error.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserViewSet(BaseViewMixin, viewsets.ModelViewSet):
    """ViewSet для управления пользователями"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
        self.auth_service = AuthService()
    
    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: UserViewSet.dispatch called - Method: {request.method}, Path: {request.path}")
        return super().dispatch(request, *args, **kwargs)
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return self.serializer_class
    
    def get_permissions(self):
        """Настройка прав доступа в зависимости от действия"""
        if self.action in ['create', 'login', 'google_login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Создание нового пользователя"""
        print(f"DEBUG: UserViewSet.create called with data: {request.data}")
        try:
            # Проверка безопасности
            security_check = self.check_security(request, f"register_{self.get_client_info(request)['ip_address']}")
            if not security_check['allowed']:
                return Response(
                    {'error': security_check['error']},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            serializer = self.get_serializer(data=request.data)
            
            # Проверяем наличие существующей pending регистрации до валидации
            existing_pending_id = None
            if hasattr(serializer, 'initial_data'):
                email = serializer.initial_data.get('email', '').lower().strip()
                # Проверяем активные pending регистрации
                from django.utils import timezone
                active_pending = PendingUserRegistration.objects.filter(
                    email=email,
                    expires_at__gt=timezone.now()
                ).first()
                
                if active_pending:
                    # Если прошло менее 5 минут, возвращаем существующий ID
                    if timezone.now() - active_pending.created_at < timezone.timedelta(minutes=5):
                        existing_pending_id = active_pending.id
            
            if not serializer.is_valid():
                print(f"DEBUG: Serializer validation errors: {serializer.errors}")
                # Если есть существующий pending ID, возвращаем его
                if existing_pending_id and 'email' not in serializer.errors:
                    return Response(
                        {
                            'message': 'Регистрация уже существует, ожидает подтверждения',
                            'pending_registration_id': existing_pending_id
                        },
                        status=status.HTTP_200_OK
                    )
                return Response(
                    {'error': 'Ошибка валидации', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Если есть существующий pending ID и валидация прошла успешно
            if existing_pending_id:
                return Response(
                    {
                        'message': 'Регистрация уже существует, ожидает подтверждения',
                        'pending_registration_id': existing_pending_id
                    },
                    status=status.HTTP_200_OK
                )
            
            # Создание pending регистрации через сериализатор
            pending_user = serializer.save()
            
            return Response(
                {
                    'message': 'Регистрация создана, ожидает подтверждения',
                    'pending_registration_id': pending_user.pending_registration_id
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return self.handle_error(e, request)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Аутентификация пользователя (email или телефон)"""
        try:
            # Получаем логин (email или телефон) и пароль
            login_field = request.data.get('email', '')  # Поле называется email для совместимости
            password = request.data.get('password', '')
            
            # Определяем, это email или телефон
            import re
            phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')  # E.164 формат
            is_phone = bool(phone_pattern.match(login_field.replace(' ', '').replace('-', '')))
            
            # Проверка безопасности
            security_check = self.check_security(request, f"login_{login_field}")
            if not security_check['allowed']:
                return Response(
                    {'error': security_check['error']},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Поиск пользователя
            user = None
            if is_phone:
                # Нормализуем телефон
                normalized_phone = login_field.strip().replace(' ', '').replace('-', '')
                if not normalized_phone.startswith('+'):
                    normalized_phone = '+' + normalized_phone
                
                try:
                    user = User.objects.get(phone=normalized_phone, is_active=True)
                except User.DoesNotExist:
                    logger.debug(f"Пользователь с телефоном {normalized_phone} не найден")
            else:
                # Поиск по email
                try:
                    user = User.objects.get(email=login_field.lower().strip(), is_active=True)
                except User.DoesNotExist:
                    logger.debug(f"Пользователь с email {login_field.lower().strip()} не найден")
            
            # Если пользователь не найден
            if not user:
                SecurityUtils.record_failed_attempt(f"login_{login_field}")
                return Response(
                    {'error': 'Неверные учетные данные'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Проверка пароля
            if not user.check_password(password):
                SecurityUtils.record_failed_attempt(f"login_{login_field}")
                return Response(
                    {'error': 'Неверные учетные данные'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Аутентификация через сервис
            client_info = self.get_client_info(request)
            result = self.auth_service.authenticate_user(
                user.email,  # Используем email для сервиса
                password,
                client_info=client_info
            )
            
            if not result['success']:
                SecurityUtils.record_failed_attempt(f"login_{login_field}")
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Сброс rate limit при успешной аутентификации
            SecurityUtils.reset_rate_limit(f"login_{login_field}")
            
            return Response({
                'message': 'Успешная аутентификация',
                'user': UserSerializer(result['user']).data,
                'token': result['tokens']['access']
            })
            
        except Exception as e:
            return self.handle_error(e, request)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Выход пользователя"""
        try:
            token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
            client_info = self.get_client_info(request)
            
            result = self.auth_service.logout_user(
                request.user,
                token=token,
                client_info=client_info
            )
            
            return Response({
                'message': 'Успешный выход'
            })
            
        except Exception as e:
            return self.handle_error(e, request)
    
    @action(detail=False, methods=['post'])
    @csrf_exempt
    def google_login(self, request):
        """Аутентификация через Google OAuth"""
        try:
            # Получаем код авторизации из запроса
            auth_code = request.data.get('code')
            redirect_uri = request.data.get('redirect_uri')
            
            if not auth_code:
                return Response(
                    {'error': 'Код авторизации не предоставлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Валидируем redirect_uri
            allowed_redirect_uris = [
                'http://localhost/auth/google/callback',
                'http://127.0.0.1/auth/google/callback',
                'https://localhost/auth/google/callback',
                'https://127.0.0.1/auth/google/callback'
            ]
            
            if not redirect_uri or redirect_uri not in allowed_redirect_uris:
                logger.error(f"Invalid redirect_uri: {redirect_uri}")
                return Response(
                    {'error': 'Недопустимый redirect URI'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверка безопасности
            security_check = self.check_security(request, f"google_login_{self.get_client_info(request)['ip_address']}")
            if not security_check['allowed']:
                return Response(
                    {'error': security_check['error']},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Обмен кода авторизации на access token
            import requests
            from django.conf import settings
            
            try:
                # Получаем Google OAuth настройки
                google_client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
                google_client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
                
                if not google_client_id or not google_client_secret:
                    return Response(
                        {'error': 'Google OAuth не настроен на сервере'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Обмениваем код на токен
                token_response = make_secure_request(
                    'https://oauth2.googleapis.com/token',
                    method='POST',
                    data={
                        'client_id': google_client_id,
                        'client_secret': google_client_secret,
                        'code': auth_code,
                        'grant_type': 'authorization_code',
                        'redirect_uri': redirect_uri,
                    }
                )
                
                if token_response.status_code != 200:
                    logger.error(f"Google token exchange failed: {token_response.text}")
                    return Response(
                        {'error': 'Не удалось обменять код авторизации на токен'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                token_data = token_response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    return Response(
                        {'error': 'Не удалось получить access token от Google'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Получаем информацию о пользователе
                user_response = make_secure_request(
                    f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}',
                    method='GET'
                )
                
                if user_response.status_code != 200:
                    return Response(
                        {'error': 'Недействительный Google токен'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                google_data = user_response.json()
                email = google_data.get('email')
                
                if not email:
                    return Response(
                        {'error': 'Не удалось получить email из Google аккаунта'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            except requests.RequestException as e:
                logger.error(f"Google OAuth request failed: {str(e)}")
                return Response(
                    {'error': 'Ошибка при проверке Google токена'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Поиск или создание пользователя
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    return Response(
                        {'error': 'Аккаунт деактивирован'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            except User.DoesNotExist:
                # Создаем нового пользователя для OAuth
                user_data = {
                    'email': email,
                    'first_name': google_data.get('given_name', ''),
                    'last_name': google_data.get('family_name', ''),
                    'is_active': True
                }
                
                client_info = self.get_client_info(request)
                result = self.user_service.create_user(
                    user_data,
                    client_info=client_info,
                    skip_password=True  # Google OAuth пользователи не имеют пароля
                )
                
                if not result['success']:
                    return Response(
                        {'error': result['error']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = result['user']
            
            # Аутентификация пользователя
            client_info = self.get_client_info(request)
            auth_result = self.auth_service.authenticate_user(
                email,
                None,  # Пароль не нужен для Google OAuth
                client_info=client_info,
                oauth_provider='google'
            )
            
            if not auth_result['success']:
                return Response(
                    {'error': auth_result['error']},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            return Response({
                'message': 'Успешная аутентификация через Google',
                'user': UserSerializer(user).data,
                'token': auth_result['tokens']['access']
            })
            
        except Exception as e:
            return self.handle_error(e, request)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Получение/обновление информации о текущем пользователе"""
        try:
            if request.method == 'GET':
                serializer = UserSerializer(request.user)
                return Response(serializer.data)
            
            else:  # PUT или PATCH
                serializer = UserUpdateSerializer(
                    request.user,
                    data=request.data,
                    partial=(request.method == 'PATCH')
                )
                
                if not serializer.is_valid():
                    return Response(
                        {'error': 'Ошибка валидации', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Обновление через сервис
                update_data = serializer.validated_data
                
                updated_user = self.user_service.update_user(
                    request.user,
                    update_data
                )
                
                return Response({
                    'message': 'Профиль успешно обновлен',
                    'user': UserSerializer(updated_user).data
                })
                
        except Exception as e:
            return self.handle_error(e, request)
    
    @action(detail=False, methods=['put'])
    def change_password(self, request):
        """Изменение пароля"""
        try:
            serializer = ChangePasswordSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Ошибка валидации', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Изменение пароля через сервис
            password_data = serializer.validated_data
            client_info = self.get_client_info(request)
            
            result = self.user_service.change_password(
                request.user,
                password_data['old_password'],
                password_data['new_password'],
                client_info=client_info
            )
            
            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': 'Пароль успешно изменен'
            })
            
        except Exception as e:
            return self.handle_error(e, request)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Запрос на сброс пароля"""
    try:
        # Проверка безопасности
        email = request.data.get('email', '')
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        security_check = SecurityUtils.check_rate_limit(f"password_reset_{email}")
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит запросов на сброс пароля'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Ошибка валидации', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Инициация сброса пароля через сервис
        auth_service = AuthService()
        result = auth_service.initiate_password_reset(
            email,
            client_info=client_info
        )
        
        # Всегда возвращаем успех для безопасности
        return Response({
            'message': 'Если указанный email существует, на него будет отправлена ссылка для сброса пароля'
        })
        
    except Exception as e:
        logger.error(f'Error in password_reset_request: {str(e)}')
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Подтверждение сброса пароля"""
    try:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Ошибка валидации', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Подтверждение сброса пароля через сервис
        reset_data = serializer.validated_data
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        auth_service = AuthService()
        result = auth_service.confirm_password_reset(
            reset_data['uid'],
            reset_data['token'],
            reset_data['new_password'],
            client_info=client_info
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Пароль успешно изменен'
        })
        
    except Exception as e:
        logger.error(f'Error in password_reset_confirm: {str(e)}')
        return Response(
            {'error': 'Внутренняя ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Telegram Views

@api_view(['GET'])
@permission_classes([AllowAny])
def telegram_bot_status(request):
    """Получение статуса Telegram бота"""
    try:
        telegram_service = TelegramService()
        stats = telegram_service.get_telegram_statistics()
        
        return Response({
            'bot_active': True,  # Здесь можно добавить реальную проверку
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f'Error in telegram_bot_status: {str(e)}')
        return Response(
            {'error': 'Ошибка получения статуса бота'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_bot_activate(request):
    """Активация Telegram бота для пользователя"""
    try:
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка безопасности
        security_check = SecurityUtils.check_rate_limit(f"telegram_activate_{email}")
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит запросов'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        telegram_service = TelegramService()
        result = telegram_service.generate_verification_code_for_user(email)
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Код верификации отправлен в Telegram',
            'verification_code': result['verification_code']
        })
        
    except Exception as e:
        logger.error(f'Error in telegram_bot_activate: {str(e)}')
        return Response(
            {'error': 'Ошибка активации бота'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def telegram_login_initiate(request):
    """Инициация входа через Telegram или регистрации нового пользователя"""
    try:
        phone_number = request.data.get('phone_number')
        verification_type = request.data.get('verification_type', 'login')
        
        if not phone_number:
            return Response(
                {'error': 'Номер телефона обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка безопасности
        security_check = SecurityUtils.check_rate_limit(f"telegram_login_{phone_number}")
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит запросов'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Нормализация номера телефона
        normalized_phone = ValidationUtils.normalize_phone_number(phone_number)
        
        # Проверяем, существует ли пользователь с нормализованным номером телефона
        try:
            user = User.objects.get(phone=normalized_phone)
            
            # Проверяем, привязан ли Telegram к аккаунту
            if not user.telegram_chat_id:
                return Response(
                    {'error': 'Telegram не привязан к данному аккаунту'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Существующий пользователь - обычный процесс входа
            telegram_service = TelegramService()
            result = telegram_service.initiate_telegram_login(
                user=user,
                phone_number=normalized_phone
            )
            
            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': 'Запрос на вход отправлен в Telegram',
                'verification_code': result.get('verification_code'),
                'user_id': user.id,
                'telegram_link': result.get('telegram_link')
            })
            
        except User.DoesNotExist:
            # Пользователь не найден - инициируем процесс регистрации
            telegram_service = TelegramService()
            
            # Создаем код верификации для регистрации
            verification_code = TelegramVerificationCode.objects.create(
                telegram_phone=normalized_phone,
                verification_type='telegram_registration',
                expires_at=timezone.now() + timezone.timedelta(minutes=10)
            )
            
            # Отправляем запрос в Telegram бот для обработки регистрации
            result = telegram_service.send_registration_request(
                phone_number=normalized_phone,
                verification_code=verification_code
            )
            
            if not result['success']:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'message': 'Запрос на регистрацию отправлен в Telegram',
                'verification_code': verification_code.code,
                'registration_mode': True,
                'telegram_link': result.get('telegram_link')
            })
        
    except Exception as e:
        logger.error(f'Error in telegram_login_initiate: {str(e)}')
        return Response(
            {'error': 'Ошибка инициации входа через Telegram'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def telegram_login_status(request):
    """Проверка статуса входа через Telegram"""
    try:
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'success': False,
                'error': 'Номер телефона обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Нормализация номера телефона
        normalized_phone = ValidationUtils.normalize_phone_number(phone_number)
        logger.info(f"Проверка статуса входа через Telegram для номера: {normalized_phone}")
        
        # Поиск пользователя по номеру телефона
        try:
            user = User.objects.get(phone=normalized_phone)
            # Поиск последнего кода верификации для входа
            verification_code = TelegramVerificationCode.objects.filter(
                user=user,
                verification_type='login',
                telegram_phone=normalized_phone
            ).order_by('-created_at').first()
        except User.DoesNotExist:
            # Пользователь не найден - ищем код верификации для регистрации
            verification_code = TelegramVerificationCode.objects.filter(
                verification_type='telegram_registration',
                telegram_phone=normalized_phone
            ).order_by('-created_at').first()
            
            if not verification_code:
                return Response({
                    'success': False,
                    'error': 'Код верификации не найден'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверка, использован ли код (создан ли пользователь)
            logger.info(f"Код верификации найден: ID={verification_code.id}, тип={verification_code.verification_type}, использован={verification_code.is_used}")
            
            if verification_code.is_used:
                # Ищем созданного пользователя
                try:
                    user = User.objects.get(phone=normalized_phone)
                    # Создание JWT токена для автоматического входа
                    from rest_framework_simplejwt.tokens import RefreshToken
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                    
                    logger.info(f"Успешная регистрация и вход через Telegram для пользователя {user.id}")
                    
                    response_data = {
                        'success': True,
                        'authenticated': True,
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': user.phone
                        }
                    }
                    logger.info(f"Возвращаем ответ с токенами: {response_data}")
                    return Response(response_data)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Ошибка создания пользователя'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.info(f"Код верификации НЕ использован, проверяем статус")
                # Проверка, не истек ли код
                if verification_code.is_expired():
                    logger.info(f"Код верификации истек")
                    return Response({
                        'success': False,
                        'authenticated': False,
                        'message': 'Код верификации истек'
                    })
                
                logger.info(f"Код верификации активен, ожидаем подтверждения")
                response_data = {
                    'success': True,
                    'authenticated': False,
                    'message': 'Ожидание подтверждения регистрации в Telegram'
                }
                logger.info(f"Возвращаем ответ ожидания: {response_data}")
                return Response(response_data)
        
        if not verification_code:
            return Response({
                'success': False,
                'authenticated': False,
                'message': 'Код верификации не найден'
            })
        
        # Проверка, использован ли код (подтвержден ли вход)
        if verification_code.is_used:
            logger.info(f"Найден использованный код верификации {verification_code.id} для пользователя {user.id if user else 'None'}")
            # Создание JWT токена для автоматического входа
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            logger.info(f"Успешный вход через Telegram для пользователя {user.id}, JWT токены созданы")
            
            return Response({
                'success': True,
                'authenticated': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone
                }
            })
        else:
            logger.info(f"Код верификации {verification_code.id} не использован для номера {normalized_phone}")
            # Проверка, не истек ли код
            if verification_code.is_expired():
                logger.info(f"Код верификации {verification_code.id} истек")
                return Response({
                    'success': False,
                    'authenticated': False,
                    'message': 'Код верификации истек'
                })
            
            logger.info(f"Ожидание подтверждения для кода {verification_code.id}")
            return Response({
                'success': True,
                'authenticated': False,
                'message': 'Ожидание подтверждения в Telegram'
            })
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса входа через Telegram: {e}")
        return Response({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_verify_code(request):
    """Верификация кода из Telegram"""
    try:
        verification_code = request.data.get('verification_code')
        phone_number = request.data.get('phone_number')
        
        if not verification_code:
            return Response(
                {'error': 'Код верификации обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not phone_number:
            return Response(
                {'error': 'Номер телефона обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        
        # Верификация кода по номеру телефона
        # Сначала пробуем QR-регистрацию, затем обычную telegram-регистрацию
        result = telegram_service.verify_code_by_phone(
            verification_code=verification_code,
            phone_number=phone_number,
            verification_type='qr_registration'
        )
        
        # Если QR-код не найден, пробуем обычную telegram-регистрацию
        if not result['success']:
            result = telegram_service.verify_code_by_phone(
                verification_code=verification_code,
                phone_number=phone_number,
                verification_type='telegram_registration'
            )
        
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Ошибка верификации кода')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = result.get('user')
        
        # Если требуется регистрация (QR-код без пользователя)
        if result.get('requires_registration'):
            return Response({
                'success': True,
                'requires_registration': True,
                'message': 'Код успешно проверен. Пожалуйста, завершите регистрацию на сайте.',
                'verification_code': result.get('verification_code', {})
            })
        
        if not user:
            return Response(
                {'error': 'Не удалось завершить регистрацию'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создание токенов
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.authtoken.models import Token
        
        # JWT токены
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Обычный токен для совместимости
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'token': token.key,  # Добавляем обычный токен
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'telegram_username': user.telegram_username,
            }
        })
        
    except Exception as e:
        logger.error(f'Error in telegram_verify_code: {str(e)}')
        return Response(
            {'error': 'Ошибка верификации кода'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_password_reset_request(request):
    """Запрос сброса пароля через Telegram"""
    try:
        telegram_username = request.data.get('telegram_username')
        if not telegram_username:
            return Response(
                {'error': 'Telegram username обязателна'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        result = telegram_service.initiate_password_reset(telegram_username)
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Код для сброса пароля отправлен в Telegram'
        })
        
    except Exception as e:
        logger.error(f'Error in telegram_password_reset_request: {str(e)}')
        return Response(
            {'error': 'Ошибка запроса сброса пароля'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def telegram_password_reset_confirm(request):
    """Подтверждение сброса пароля через Telegram"""
    try:
        verification_code = request.data.get('verification_code')
        new_password = request.data.get('new_password')
        
        if not verification_code or not new_password:
            return Response(
                {'error': 'Код верификации и новый пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        result = telegram_service.confirm_password_reset(
            verification_code,
            new_password
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Пароль успешно изменен через Telegram'
        })
        
    except Exception as e:
        logger.error(f'Error in telegram_password_reset_confirm: {str(e)}')
        return Response(
            {'error': 'Ошибка подтверждения сброса пароля'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Phone Change Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_current_phone_code(request):
    """Отправка кода для подтверждения текущего номера телефона"""
    try:
        user = request.user
        
        if not user.phone:
            return Response(
                {'error': 'У вас не указан номер телефона в профиле'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка безопасности - ограничение по количеству запросов
        security_check = SecurityUtils.check_rate_limit(
            f"phone_change_code_{user.id}",
            max_attempts=3,
            window_minutes=15
        )
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит запросов на отправку кода'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        telegram_service = TelegramService()
        result = telegram_service.send_phone_change_code(
            user=user,
            verification_type='phone_change_current'
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Код отправлен в ваш Telegram бот'
        })
        
    except Exception as e:
        logger.error(f'Error in send_current_phone_code: {str(e)}')
        return Response(
            {'error': 'Ошибка отправки кода'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_current_phone_code(request):
    """Проверка кода для текущего номера телефона"""
    try:
        user = request.user
        verification_code = request.data.get('verification_code')
        
        if not verification_code:
            return Response(
                {'error': 'Код верификации обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        result = telegram_service.verify_phone_change_code(
            user=user,
            verification_code=verification_code,
            verification_type='phone_change_current'
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Текущий номер подтвержден'
        })
        
    except Exception as e:
        logger.error(f'Error in verify_current_phone_code: {str(e)}')
        return Response(
            {'error': 'Ошибка проверки кода'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_phone_change(request):
    """Запрос на смену номера телефона"""
    try:
        user = request.user
        new_phone_number = request.data.get('new_phone_number')
        
        if not new_phone_number:
            return Response(
                {'error': 'Новый номер телефона обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Нормализация номера
        normalized_phone = ValidationUtils.normalize_phone_number(new_phone_number)
        
        # Проверка, не используется ли номер другим пользователем
        if User.objects.filter(phone=normalized_phone).exclude(id=user.id).exists():
            return Response(
                {'error': 'Этот номер телефона уже используется другим пользователем'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка, что новый номер отличается от текущего
        if user.phone and ValidationUtils.normalize_phone_number(user.phone) == normalized_phone:
            return Response(
                {'error': 'Новый номер должен отличаться от текущего'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        result = telegram_service.initiate_phone_change(
            user=user,
            new_phone_number=normalized_phone
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Ссылка для подтверждения смены номера создана',
            'telegram_link': result['telegram_link']
        })
        
    except Exception as e:
        logger.error(f'Error in request_phone_change: {str(e)}')
        return Response(
            {'error': 'Ошибка запроса смены номера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def phone_change_status(request):
    """Проверка статуса смены номера телефона"""
    try:
        user = request.user
        
        telegram_service = TelegramService()
        result = telegram_service.check_phone_change_status(user=user)
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'is_completed': result['is_completed'],
            'new_phone_number': result.get('new_phone_number')
        })
        
    except Exception as e:
        logger.error(f'Error in phone_change_status: {str(e)}')
        return Response(
            {'error': 'Ошибка проверки статуса'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# QR Code Views

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def create_qr_code(request):
    """Создание QR кода"""
    try:
        qr_type = request.data.get('type', 'registration')
        description = request.data.get('description', '')
        pending_registration_id = request.data.get('pending_registration_id')
        
        # Проверка безопасности
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        security_check = SecurityUtils.check_rate_limit(
            f"qr_create_{client_info['ip_address']}",
            max_attempts=10,
            window_minutes=60
        )
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит создания QR кодов'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        qr_service = QRService()
        # Динамически определяем base_url на основе запроса
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        base_url = f'{scheme}://{host}'
        
        result = qr_service.create_qr_code(
            base_url=base_url,
            pending_registration_id=pending_registration_id
        )
        
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Ошибка создания QR кода')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        qr_code = result['qr_code']
        
        # Формируем ответ
        qr_data = {
            'qr_id': str(qr_code.qr_id),
            'trigger_url': qr_code.trigger_url,
            'telegram_bot_url': qr_code.telegram_bot_url,
            'type': qr_type,
            'description': description
        }
        
        return Response({
            'message': 'QR код успешно создан',
            'qr_code': str(qr_code.qr_id),
            'qr_data': qr_data
        })
        
    except Exception as e:
        logger.error(f'Error in create_qr_code: {str(e)}')
        return Response(
            {'error': 'Ошибка создания QR кода'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@require_http_methods(["GET"])
def qr_trigger(request, qr_id):
    """Обработка сканирования QR кода"""
    try:
        logger.info(f"QR trigger accessed: {qr_id}")
        
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        qr_service = QRService()
        result = qr_service.process_qr_trigger(
            str(qr_id),
            client_info.get('ip_address'),
            client_info.get('user_agent')
        )
        
        if not result['success']:
            logger.error(f"QR trigger failed: {result.get('error')}")
            return JsonResponse(
                {'error': result.get('error', 'Неверный QR код')},
                status=400
            )
        
        qr_code = result['qr_code']
        
        # Отмечаем активацию триггера
        qr_service.activate_qr_trigger(str(qr_id))
        
        # Получаем username бота из настроек или используем значение по умолчанию
        bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GuschaBot')
        
        # Перенаправление на Telegram бота
        if qr_code and qr_code.telegram_bot_url:
            redirect_url = qr_code.telegram_bot_url
        else:
            redirect_url = f'https://t.me/{bot_username}'
        
        logger.info(f"Redirecting to Telegram bot: {redirect_url}")
        return HttpResponseRedirect(redirect_url)
        
    except Exception as e:
        logger.error(f'Error in qr_trigger: {str(e)}')
        return JsonResponse(
            {'error': 'Ошибка обработки QR кода'},
            status=500
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def qr_status(request, qr_id):
    """Получение статуса QR кода"""
    try:
        qr_service = QRService()
        qr_status = qr_service.get_qr_status(qr_id)
        
        if not qr_status:
            return Response(
                {'error': 'QR код не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'status': 'active' if qr_status.get('is_complete_flow') else 'pending',
            'qr_data': qr_status
        })
        
    except Exception as e:
        logger.error(f'Error in qr_status: {str(e)}')
        return Response(
            {'error': 'Ошибка получения статуса QR кода'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def qr_bot_started(request):
    """Отметка о запуске бота через QR код"""
    try:
        qr_id = request.data.get('qr_id')
        telegram_chat_id = request.data.get('telegram_chat_id')
        
        # Проверка авторизации
        client_ip = SecurityUtils.get_client_ip(request)
        if not SecurityUtils.is_ip_allowed(client_ip):
            return Response(
                {'error': 'Неавторизованный доступ'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not qr_id or not telegram_chat_id:
            return Response(
                {'error': 'QR ID и Telegram Chat ID обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        qr_service = QRService()
        result = qr_service.mark_bot_started(
            qr_id,
            telegram_chat_id
        )
        
        if not result['success']:
            return Response(
                {'error': result.get('error', 'Ошибка отметки запуска бота')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification_code = result.get('verification_code')
        
        display_code = verification_code.generate_secure_code() if verification_code else None
        return Response({
            'message': 'Запуск бота отмечен',
            'verification_code': display_code
        })
        
    except Exception as e:
        logger.error(f'Error in qr_bot_started: {str(e)}')
        return Response(
            {'error': 'Ошибка отметки запуска бота'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Дополнительные API endpoints

@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token(request):
    """Получение CSRF токена"""
    return Response({
        'csrfToken': request.META.get('CSRF_COOKIE', '')
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_statistics(request):
    """Получение статистики пользователя"""
    try:
        user_service = UserService()
        stats = user_service.get_user_statistics(request.user)
        
        return Response({
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f'Error in user_statistics: {str(e)}')
        return Response(
            {'error': 'Ошибка получения статистики'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_telegram(request):
    """Привязка Telegram аккаунта"""
    try:
        telegram_username = request.data.get('telegram_username')
        telegram_chat_id = request.data.get('telegram_chat_id')
        
        if not telegram_username or not telegram_chat_id:
            return Response(
                {'error': 'Telegram username и chat ID обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        telegram_service = TelegramService()
        success = telegram_service.link_telegram_to_user(
            request.user,
            telegram_chat_id,
            telegram_username
        )
        
        result = {'success': success}
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Telegram аккаунт успешно привязан'
        })
        
    except Exception as e:
        logger.error(f'Error in link_telegram: {str(e)}')
        return Response(
            {'error': 'Ошибка привязки Telegram аккаунта'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlink_telegram(request):
    """Отвязка Telegram аккаунта"""
    try:
        telegram_service = TelegramService()
        success = telegram_service.unlink_telegram_from_user(request.user)
        
        result = {'success': success}
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Telegram аккаунт успешно отвязан'
        })
        
    except Exception as e:
        logger.error(f'Error in unlink_telegram: {str(e)}')
        return Response(
            {'error': 'Ошибка отвязки Telegram аккаунта'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def authenticated_password_reset(request):
    """Сброс пароля для авторизованного пользователя через Telegram"""
    try:
        # Проверка безопасности
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        security_check = SecurityUtils.check_rate_limit(
            f"auth_password_reset_{request.user.id}",
            max_attempts=3,
            window_minutes=60
        )
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит запросов на сброс пароля'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        telegram_service = TelegramService()
        result = telegram_service.initiate_authenticated_password_reset(
            user=request.user,
            request=request
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Ссылка для сброса пароля отправлена в Telegram',
            'token_id': result.get('token_id')
        })
        
    except Exception as e:
        logger.error(f'Error in authenticated_password_reset: {str(e)}')
        return Response(
            {'error': 'Ошибка при инициации сброса пароля'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset_token(request):
    """Подтверждение сброса пароля по токену"""
    try:
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not token or not new_password:
            return Response(
                {'error': 'Токен и новый пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка безопасности
        client_info = {
            'ip_address': SecurityUtils.get_client_ip(request),
            'user_agent': SecurityUtils.get_user_agent(request)
        }
        
        security_check = SecurityUtils.check_rate_limit(
            f"confirm_password_reset_{client_info['ip_address']}",
            max_attempts=5,
            window_minutes=60
        )
        if not security_check['allowed']:
            return Response(
                {'error': 'Превышен лимит попыток подтверждения'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        telegram_service = TelegramService()
        result = telegram_service.confirm_password_reset_with_token(
            token=token,
            new_password=new_password,
            client_info=client_info
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Пароль успешно изменен'
        })
        
    except Exception as e:
        logger.error(f'Error in confirm_password_reset_token: {str(e)}')
        return Response(
            {'error': 'Ошибка при подтверждении сброса пароля'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# Добавить timeout ко всем requests
DEFAULT_TIMEOUT = 10  # Уменьшен с 30 до 10 секунд

def make_secure_request(url, method='GET', max_retries=3, **kwargs):
    """Безопасный wrapper для HTTP запросов с retry логикой"""
    kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
    kwargs.setdefault('verify', True)  # Проверка SSL
    
    # Настройка retry стратегии для SSL ошибок
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        allowed_methods=["HEAD", "GET", "POST"]
    )
    
    # Создаем сессию с retry адаптером
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Явно передаем timeout для Bandit
    timeout = kwargs.get('timeout', DEFAULT_TIMEOUT)
    
    try:
        if method.upper() == 'POST':
            return session.post(url, timeout=timeout, **{k: v for k, v in kwargs.items() if k != 'timeout'})
        elif method.upper() == 'GET':
            return session.get(url, timeout=timeout, **{k: v for k, v in kwargs.items() if k != 'timeout'})
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL Error for {url}: {str(e)}")
        # Повторная попытка с отключенной проверкой SSL только для Google API
        if 'googleapis.com' in url:
            logger.warning(f"Retrying {url} with SSL verification disabled")
            kwargs['verify'] = False
            if method.upper() == 'POST':
                return session.post(url, timeout=timeout, **{k: v for k, v in kwargs.items() if k != 'timeout'})
            elif method.upper() == 'GET':
                return session.get(url, timeout=timeout, **{k: v for k, v in kwargs.items() if k != 'timeout'})
        raise
    finally:
        session.close()
