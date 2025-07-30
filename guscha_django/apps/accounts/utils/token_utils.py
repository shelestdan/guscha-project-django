from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any, Tuple
import jwt
import secrets
import string
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TokenUtils:
    """Утилиты для работы с токенами"""
    
    # Константы
    DEFAULT_TOKEN_LENGTH = 32
    DEFAULT_JWT_EXPIRY_HOURS = 24
    DEFAULT_REFRESH_TOKEN_EXPIRY_DAYS = 30
    
    @staticmethod
    def generate_random_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
        """Генерация случайного токена"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_secure_token(length: int = DEFAULT_TOKEN_LENGTH) -> str:
        """Генерация криптографически стойкого токена"""
        return secrets.token_urlsafe(length)[:length]
    
    @staticmethod
    def generate_numeric_token(length: int = 6) -> str:
        """Генерация числового токена"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Хеширование токена"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_token_hash(token: str, token_hash: str) -> bool:
        """Проверка хеша токена"""
        return hashlib.sha256(token.encode()).hexdigest() == token_hash
    
    @staticmethod
    def create_jwt_token(user_id: int, payload: Dict[str, Any] = None, expiry_hours: int = DEFAULT_JWT_EXPIRY_HOURS) -> str:
        """Создание JWT токена"""
        try:
            now = timezone.now()
            exp_time = now + timedelta(hours=expiry_hours)
            
            jwt_payload = {
                'user_id': user_id,
                'iat': int(now.timestamp()),
                'exp': int(exp_time.timestamp()),
                'type': 'access'
            }
            
            if payload:
                jwt_payload.update(payload)
            
            secret_key = getattr(settings, 'SECRET_KEY')
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            
            token = jwt.encode(jwt_payload, secret_key, algorithm=algorithm)
            
            logger.info(f'JWT token created for user {user_id}')
            return token
            
        except Exception as e:
            logger.error(f'Failed to create JWT token for user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def create_refresh_token(user_id: int, expiry_days: int = DEFAULT_REFRESH_TOKEN_EXPIRY_DAYS) -> str:
        """Создание refresh токена"""
        try:
            now = timezone.now()
            exp_time = now + timedelta(days=expiry_days)
            
            payload = {
                'user_id': user_id,
                'iat': int(now.timestamp()),
                'exp': int(exp_time.timestamp()),
                'type': 'refresh'
            }
            
            secret_key = getattr(settings, 'SECRET_KEY')
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            
            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            
            logger.info(f'Refresh token created for user {user_id}')
            return token
            
        except Exception as e:
            logger.error(f'Failed to create refresh token for user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Декодирование JWT токена"""
        try:
            secret_key = getattr(settings, 'SECRET_KEY')
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            
            # Проверяем срок действия
            exp_timestamp = payload.get('exp')
            if exp_timestamp and datetime.fromtimestamp(exp_timestamp) < datetime.now():
                logger.warning('JWT token has expired')
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning('JWT token has expired')
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f'Invalid JWT token: {str(e)}')
            return None
        except Exception as e:
            logger.error(f'Failed to decode JWT token: {str(e)}')
            return None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Проверка истечения срока действия токена"""
        payload = TokenUtils.decode_jwt_token(token)
        if not payload:
            return True
        
        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return False
        
        return datetime.fromtimestamp(exp_timestamp) < datetime.now()
    
    @staticmethod
    def get_token_expiry_time(token: str) -> Optional[datetime]:
        """Получение времени истечения токена"""
        payload = TokenUtils.decode_jwt_token(token)
        if not payload:
            return None
        
        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return None
        
        return datetime.fromtimestamp(exp_timestamp)
    
    @staticmethod
    def refresh_jwt_token(refresh_token: str) -> Optional[Tuple[str, str]]:
        """Обновление JWT токена с помощью refresh токена"""
        try:
            payload = TokenUtils.decode_jwt_token(refresh_token)
            if not payload:
                return None
            
            # Проверяем тип токена
            if payload.get('type') != 'refresh':
                logger.warning('Invalid token type for refresh')
                return None
            
            user_id = payload.get('user_id')
            if not user_id:
                logger.warning('No user_id in refresh token')
                return None
            
            # Создаем новые токены
            new_access_token = TokenUtils.create_jwt_token(user_id)
            new_refresh_token = TokenUtils.create_refresh_token(user_id)
            
            logger.info(f'JWT tokens refreshed for user {user_id}')
            return new_access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f'Failed to refresh JWT token: {str(e)}')
            return None
    
    @staticmethod
    def create_password_reset_token(user) -> str:
        """Создание токена для сброса пароля"""
        try:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            
            logger.info(f'Password reset token created for user {user.id}')
            return token
            
        except Exception as e:
            logger.error(f'Failed to create password reset token for user {user.id}: {str(e)}')
            raise
    
    @staticmethod
    def verify_password_reset_token(user, token: str) -> bool:
        """Проверка токена для сброса пароля"""
        try:
            token_generator = PasswordResetTokenGenerator()
            is_valid = token_generator.check_token(user, token)
            
            if is_valid:
                logger.info(f'Password reset token verified for user {user.id}')
            else:
                logger.warning(f'Invalid password reset token for user {user.id}')
            
            return is_valid
            
        except Exception as e:
            logger.error(f'Failed to verify password reset token for user {user.id}: {str(e)}')
            return False
    
    @staticmethod
    def create_uid_from_user(user) -> str:
        """Создание UID из пользователя"""
        try:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            return uid.decode()
            
        except Exception as e:
            logger.error(f'Failed to create UID for user {user.id}: {str(e)}')
            raise
    
    @staticmethod
    def decode_uid_to_user_id(uid: str) -> Optional[int]:
        """Декодирование UID в ID пользователя"""
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            return int(user_id)
            
        except (TypeError, ValueError, OverflowError) as e:
            logger.warning(f'Failed to decode UID {uid}: {str(e)}')
            return None
    
    @staticmethod
    def create_activation_token(user) -> str:
        """Создание токена для активации аккаунта"""
        try:
            # Используем тот же генератор, что и для сброса пароля
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            
            logger.info(f'Activation token created for user {user.id}')
            return token
            
        except Exception as e:
            logger.error(f'Failed to create activation token for user {user.id}: {str(e)}')
            raise
    
    @staticmethod
    def verify_activation_token(user, token: str) -> bool:
        """Проверка токена для активации аккаунта"""
        try:
            token_generator = PasswordResetTokenGenerator()
            is_valid = token_generator.check_token(user, token)
            
            if is_valid:
                logger.info(f'Activation token verified for user {user.id}')
            else:
                logger.warning(f'Invalid activation token for user {user.id}')
            
            return is_valid
            
        except Exception as e:
            logger.error(f'Failed to verify activation token for user {user.id}: {str(e)}')
            return False
    
    @staticmethod
    def create_api_key(user_id: int, name: str = '', permissions: list = None) -> Dict[str, Any]:
        """Создание API ключа"""
        try:
            api_key = TokenUtils.generate_secure_token(40)
            api_secret = TokenUtils.generate_secure_token(64)
            
            # Хешируем секрет для хранения
            secret_hash = TokenUtils.hash_token(api_secret)
            
            key_data = {
                'api_key': api_key,
                'api_secret': api_secret,  # Возвращаем только один раз
                'secret_hash': secret_hash,  # Для хранения в БД
                'user_id': user_id,
                'name': name,
                'permissions': permissions or [],
                'created_at': timezone.now().isoformat()
            }
            
            logger.info(f'API key created for user {user_id}')
            return key_data
            
        except Exception as e:
            logger.error(f'Failed to create API key for user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def verify_api_key(api_key: str, api_secret: str, stored_secret_hash: str) -> bool:
        """Проверка API ключа"""
        try:
            return TokenUtils.verify_token_hash(api_secret, stored_secret_hash)
            
        except Exception as e:
            logger.error(f'Failed to verify API key: {str(e)}')
            return False
    
    @staticmethod
    def create_session_token(user_id: int, session_data: Dict[str, Any] = None) -> str:
        """Создание токена сессии"""
        try:
            payload = {
                'user_id': user_id,
                'session_id': TokenUtils.generate_random_token(16),
                'created_at': timezone.now().isoformat(),
                'type': 'session'
            }
            
            if session_data:
                payload.update(session_data)
            
            # Создаем JWT токен без срока истечения для сессии
            secret_key = getattr(settings, 'SECRET_KEY')
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            
            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            
            logger.info(f'Session token created for user {user_id}')
            return token
            
        except Exception as e:
            logger.error(f'Failed to create session token for user {user_id}: {str(e)}')
            raise
    
    @staticmethod
    def invalidate_token(token: str) -> bool:
        """Инвалидация токена (добавление в черный список)"""
        try:
            # Здесь можно реализовать логику добавления токена в черный список
            # Например, сохранить в Redis или базе данных
            
            # Пока что просто логируем
            payload = TokenUtils.decode_jwt_token(token)
            if payload:
                user_id = payload.get('user_id')
                logger.info(f'Token invalidated for user {user_id}')
                return True
            
            return False
            
        except Exception as e:
            logger.error(f'Failed to invalidate token: {str(e)}')
            return False
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Проверка, находится ли токен в черном списке"""
        try:
            # Здесь можно реализовать проверку черного списка
            # Например, проверить в Redis или базе данных
            
            # Пока что возвращаем False
            return False
            
        except Exception as e:
            logger.error(f'Failed to check token blacklist: {str(e)}')
            return True  # В случае ошибки считаем токен недействительным
    
    @staticmethod
    def get_token_info(token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о токене"""
        payload = TokenUtils.decode_jwt_token(token)
        if not payload:
            return None
        
        exp_timestamp = payload.get('exp')
        iat_timestamp = payload.get('iat')
        
        return {
            'user_id': payload.get('user_id'),
            'type': payload.get('type'),
            'issued_at': datetime.fromtimestamp(iat_timestamp) if iat_timestamp else None,
            'expires_at': datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None,
            'is_expired': TokenUtils.is_token_expired(token),
            'is_blacklisted': TokenUtils.is_token_blacklisted(token)
        }
    
    @staticmethod
    def validate_token_format(token: str) -> bool:
        """Проверка формата токена"""
        if not token or not isinstance(token, str):
            return False
        
        # Проверяем минимальную длину
        if len(token) < 10:
            return False
        
        # Для JWT токенов проверяем структуру
        if '.' in token:
            parts = token.split('.')
            if len(parts) != 3:
                return False
        
        return True
    
    @staticmethod
    def clean_expired_tokens() -> int:
        """Очистка истекших токенов (заглушка для будущей реализации)"""
        # Здесь можно реализовать логику очистки истекших токенов
        # из черного списка или базы данных
        
        logger.info('Token cleanup completed')
        return 0
    
    @staticmethod
    def get_token_statistics() -> Dict[str, Any]:
        """Получение статистики токенов (заглушка для будущей реализации)"""
        return {
            'total_active_tokens': 0,
            'total_expired_tokens': 0,
            'total_blacklisted_tokens': 0,
            'tokens_created_today': 0
        }