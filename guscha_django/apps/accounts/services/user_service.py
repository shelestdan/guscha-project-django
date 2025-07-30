from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any
import logging

from ..models import PendingUserRegistration
from ..validators import UserValidator
from ..repositories import UserRepository

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Сервис для управления пользователями"""
    
    def __init__(self):
        self.user_repository = UserRepository()
        self.user_validator = UserValidator()
    
    def create_user(self, user_data: Dict[str, Any], skip_password: bool = False, client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Создание нового пользователя"""
        try:
            # Валидация данных (пропускаем валидацию пароля для OAuth)
            if not skip_password:
                self.user_validator.validate_user_creation_data(user_data)
            
            with transaction.atomic():
                # Создание пользователя
                user = self.user_repository.create_user(
                    email=user_data['email'],
                    password=user_data.get('password'),
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    phone=user_data.get('phone', ''),
                    address=user_data.get('address', ''),
                    skip_password=skip_password
                )
                
                logger.info(f"Пользователь создан: {user.email} (OAuth: {skip_password})")
                return {
                    'success': True,
                    'user': user
                }
                
        except ValidationError as e:
            logger.error(f"Ошибка валидации при создании пользователя: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}")
            return {
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }
    
    def update_user(self, user: User, update_data: Dict[str, Any]) -> User:
        """Обновление данных пользователя"""
        try:
            # Валидация данных обновления
            self.user_validator.validate_user_update_data(update_data)
            
            with transaction.atomic():
                updated_user = self.user_repository.update_user(user, update_data)
                logger.info(f"Пользователь обновлен: {user.email}")
                return updated_user
                
        except ValidationError as e:
            logger.error(f"Ошибка валидации при обновлении пользователя: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя: {e}")
            raise
    
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """Изменение пароля пользователя"""
        try:
            # Проверка старого пароля
            if not user.check_password(old_password):
                raise ValidationError(_("Неверный текущий пароль"))
            
            # Валидация нового пароля
            self.user_validator.validate_password(new_password)
            
            with transaction.atomic():
                user.set_password(new_password)
                user.save()
                logger.info(f"Пароль изменен для пользователя: {user.email}")
                return True
                
        except ValidationError as e:
            logger.error(f"Ошибка при изменении пароля: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при изменении пароля: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        return self.user_repository.get_by_email(email)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        return self.user_repository.get_by_id(user_id)
    
    def get_active_users(self):
        """Получение активных пользователей"""
        return self.user_repository.get_active_users()
    
    def deactivate_user(self, user: User) -> bool:
        """Деактивация пользователя"""
        try:
            with transaction.atomic():
                user.is_active = False
                user.save()
                logger.info(f"Пользователь деактивирован: {user.email}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при деактивации пользователя: {e}")
            raise
    
    def activate_user(self, user: User) -> bool:
        """Активация пользователя"""
        try:
            with transaction.atomic():
                user.is_active = True
                user.save()
                logger.info(f"Пользователь активирован: {user.email}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при активации пользователя: {e}")
            raise
    
    def create_pending_registration(self, user_data: Dict[str, Any]) -> PendingUserRegistration:
        """Создание записи ожидающей регистрации"""
        try:
            # Валидация данных
            self.user_validator.validate_user_creation_data(user_data)
            
            with transaction.atomic():
                pending_registration = self.user_repository.create_pending_registration(user_data)
                logger.info(f"Создана запись ожидающей регистрации: {pending_registration.email}")
                return pending_registration
                
        except ValidationError as e:
            logger.error(f"Ошибка валидации при создании ожидающей регистрации: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании ожидающей регистрации: {e}")
            raise
    
    def complete_registration_from_pending(self, pending_registration: PendingUserRegistration) -> User:
        """Завершение регистрации из ожидающей записи"""
        try:
            with transaction.atomic():
                # Создание пользователя из ожидающей записи
                user = self.user_repository.create_user_from_pending(pending_registration)
                
                # Удаление ожидающей записи
                pending_registration.delete()
                
                logger.info(f"Регистрация завершена для пользователя: {user.email}")
                return user
                
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации: {e}")
            raise
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Получение статистики пользователей"""
        return self.user_repository.get_user_statistics()