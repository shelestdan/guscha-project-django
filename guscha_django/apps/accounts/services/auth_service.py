from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password, ValidationError as PasswordValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from typing import Optional, Dict, Any, Tuple
import logging

from ..models import User
from ..validators import AuthValidator
from ..repositories import UserRepository
from ..utils import EmailUtils

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис для управления аутентификацией"""
    
    def __init__(self):
        self.user_repository = UserRepository()
        self.auth_validator = AuthValidator()
        self.email_utils = EmailUtils()
    
    def authenticate_user(self, email: str, password: str = None, client_info: Dict[str, Any] = None, oauth_provider: str = None) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        try:
            # Для OAuth аутентификации пропускаем валидацию пароля
            if oauth_provider:
                try:
                    user = User.objects.get(email=email, is_active=True)
                except User.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Пользователь не найден'
                    }
            else:
                # Валидация входных данных для обычной аутентификации
                if not password:
                    return {
                        'success': False,
                        'error': 'Пароль обязателен'
                    }
                
                self.auth_validator.validate_login_data({'email': email, 'password': password})
                
                # Аутентификация
                user = authenticate(username=email, password=password)
                
                if not user or not user.is_active:
                    logger.warning(f"Неудачная попытка аутентификации: {email}")
                    return {
                        'success': False,
                        'error': 'Неверные учетные данные'
                    }
            
            # Создание или получение токена
            token, created = Token.objects.get_or_create(user=user)
            
            # Обновление времени последнего входа
            self.user_repository.update_last_login(user)
            
            logger.info(f"Успешная аутентификация пользователя: {email} (OAuth: {oauth_provider or 'нет'})")
            
            return {
                'success': True,
                'user': user,
                'tokens': {
                    'access': token.key,
                    'token_type': 'Bearer'
                }
            }
                
        except ValidationError as e:
            logger.error(f"Ошибка валидации при аутентификации: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            return {
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }
    
    def login_user(self, request, user: User) -> Token:
        """Вход пользователя в систему"""
        try:
            # Вход в систему
            login(request, user)
            
            # Создание или получение токена
            token, created = Token.objects.get_or_create(user=user)
            
            logger.info(f"Пользователь вошел в систему: {user.email}")
            return token
            
        except Exception as e:
            logger.error(f"Ошибка при входе в систему: {e}")
            raise
    
    def logout_user(self, user: User, token: str = None, client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выход пользователя из системы"""
        try:
            # Удаление токена
            if token:
                Token.objects.filter(user=user, key=token).delete()
            else:
                Token.objects.filter(user=user).delete()
            
            logger.info(f"Пользователь вышел из системы: {user.email}")
            return {
                'success': True,
                'message': 'Успешный выход'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при выходе из системы: {e}")
            return {
                'success': False,
                'error': 'Ошибка при выходе из системы'
            }
    
    def initiate_password_reset(self, email: str) -> bool:
        """Инициация сброса пароля"""
        try:
            # Поиск пользователя
            user = self.user_repository.get_by_email(email)
            if not user:
                # Не раскрываем информацию о существовании пользователя
                logger.warning(f"Попытка сброса пароля для несуществующего email: {email}")
                return True
            
            # Генерация токена сброса
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Отправка email
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            success = self.email_utils.send_password_reset_email(
                user.email,
                user.get_full_name() or user.email,
                reset_url
            )
            
            if success:
                logger.info(f"Email сброса пароля отправлен: {email}")
            else:
                logger.error(f"Ошибка отправки email сброса пароля: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при инициации сброса пароля: {e}")
            raise
    
    def confirm_password_reset(self, uid: str, token: str, new_password: str) -> bool:
        """Подтверждение сброса пароля"""
        try:
            # Валидация нового пароля
            self.auth_validator.validate_password(new_password)
            
            # Декодирование UID
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = self.user_repository.get_by_id(int(user_id))
            except (TypeError, ValueError, OverflowError):
                raise ValidationError(_("Неверная ссылка сброса пароля"))
            
            if not user:
                raise ValidationError(_("Пользователь не найден"))
            
            # Проверка токена
            if not default_token_generator.check_token(user, token):
                raise ValidationError(_("Неверный или истекший токен"))
            
            # Установка нового пароля
            with transaction.atomic():
                try:
                    validate_password(new_password, user=user)
                except PasswordValidationError as e:
                    raise ValidationError(str(e))
                user.set_password(new_password)
                user.save()
                
                # Удаление всех токенов пользователя
                Token.objects.filter(user=user).delete()
            
            logger.info(f"Пароль успешно сброшен для пользователя: {user.email}")
            return True
            
        except ValidationError as e:
            logger.error(f"Ошибка валидации при сбросе пароля: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при сбросе пароля: {e}")
            raise
    
    def validate_token(self, token_key: str) -> Optional[User]:
        """Валидация токена аутентификации"""
        try:
            token = Token.objects.select_related('user').get(key=token_key)
            if token.user.is_active:
                return token.user
            return None
        except Token.DoesNotExist:
            return None
    
    def refresh_token(self, user: User) -> Token:
        """Обновление токена пользователя"""
        try:
            # Удаление старого токена
            Token.objects.filter(user=user).delete()
            
            # Создание нового токена
            token = Token.objects.create(user=user)
            
            logger.info(f"Токен обновлен для пользователя: {user.email}")
            return token
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            raise
    
    def get_user_sessions_info(self, user: User) -> Dict[str, Any]:
        """Получение информации о сессиях пользователя"""
        try:
            token_exists = Token.objects.filter(user=user).exists()
            
            return {
                'user_id': user.id,
                'email': user.email,
                'is_active': user.is_active,
                'has_active_token': token_exists,
                'last_login': user.last_login,
                'date_joined': user.date_joined
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о сессиях: {e}")
            raise
    
    def revoke_all_tokens(self, user: User) -> bool:
        """Отзыв всех токенов пользователя"""
        try:
            deleted_count = Token.objects.filter(user=user).delete()[0]
            logger.info(f"Отозвано {deleted_count} токенов для пользователя: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отзыве токенов: {e}")
            raise