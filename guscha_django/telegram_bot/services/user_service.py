"""Сервис для работы с пользователями."""

import logging
from typing import Optional, Tuple

from apps.accounts.models import User
from ..repositories import UserRepository
from ..exceptions import UserNotFoundError, ValidationError, DatabaseError
from ..utils.validators import PhoneValidator, ValidationResult
from ..utils.helpers import get_user_display_name, hash_phone_number

logger = logging.getLogger(__name__)


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    async def get_user_by_chat_id(self, chat_id: str) -> Optional[User]:
        """Получает пользователя по Telegram chat_id."""
        try:
            return await self.user_repo.get_by_chat_id(chat_id)
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по chat_id {chat_id}: {e}")
            raise UserNotFoundError(f"Пользователь не найден: {e}")
    
    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Получает пользователя по номеру телефона."""
        try:
            # Валидируем номер телефона
            validation_result = PhoneValidator.validate_phone(phone)
            if not validation_result.is_valid:
                raise ValidationError(
                    f"Некорректный номер телефона: {', '.join(validation_result.errors)}",
                    field="phone",
                    value=phone
                )
            
            return await self.user_repo.get_by_phone(validation_result.normalized_value)
        except ValidationError:
            raise
        except Exception as e:
            phone_hash = hash_phone_number(phone)
            logger.error(f"Ошибка получения пользователя по телефону {phone_hash}: {e}")
            raise UserNotFoundError(f"Пользователь не найден: {e}")
    
    async def create_telegram_user(
        self,
        phone: str,
        chat_id: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Создает нового пользователя через Telegram."""
        try:
            # Валидируем входные данные
            phone_validation = PhoneValidator.validate_phone(phone)
            if not phone_validation.is_valid:
                raise ValidationError(
                    f"Некорректный номер телефона: {', '.join(phone_validation.errors)}",
                    field="phone",
                    value=phone
                )
            
            if not chat_id or not chat_id.strip():
                raise ValidationError("Chat ID не может быть пустым", field="chat_id", value=chat_id)
            
            # Проверяем, не существует ли уже пользователь
            existing_user = await self.user_repo.get_by_phone(phone_validation.normalized_value)
            if existing_user:
                raise ValidationError(
                    "Пользователь с таким номером телефона уже существует",
                    field="phone",
                    value=phone
                )
            
            existing_chat_user = await self.user_repo.get_by_chat_id(chat_id)
            if existing_chat_user:
                raise ValidationError(
                    "Этот Telegram аккаунт уже привязан к другому пользователю",
                    field="chat_id",
                    value=chat_id
                )
            
            # Создаем пользователя
            user = await self.user_repo.create_telegram_user(
                phone=phone_validation.normalized_value,
                chat_id=chat_id,
                telegram_username=telegram_username,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            phone_hash = hash_phone_number(phone)
            logger.info(f"Создан новый пользователь через Telegram: {user.id}, телефон: {phone_hash}")
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            phone_hash = hash_phone_number(phone)
            logger.error(f"Ошибка создания пользователя через Telegram для {phone_hash}: {e}")
            raise DatabaseError(f"Ошибка создания пользователя: {e}")
    
    async def update_telegram_info(
        self,
        user: User,
        chat_id: str,
        username: Optional[str] = None
    ) -> None:
        """Обновляет Telegram информацию пользователя."""
        try:
            await self.user_repo.update_telegram_info(user, chat_id, username)
            logger.info(f"Обновлена Telegram информация для пользователя {user.id}")
        except Exception as e:
            logger.error(f"Ошибка обновления Telegram информации для пользователя {user.id}: {e}")
            raise DatabaseError(f"Ошибка обновления информации: {e}")
    
    async def verify_phone_match(
        self,
        user: User,
        telegram_phone: str
    ) -> Tuple[bool, Optional[str]]:
        """Проверяет совпадение номера телефона пользователя с номером из Telegram."""
        try:
            if not user.phone:
                return False, "У пользователя не указан номер телефона"
            
            # Проверяем совпадение номеров
            validation_result = PhoneValidator.validate_phone_match(telegram_phone, user.phone)
            
            if validation_result.is_valid:
                return True, None
            else:
                return False, ", ".join(validation_result.errors)
                
        except Exception as e:
            logger.error(f"Ошибка проверки совпадения номеров для пользователя {user.id}: {e}")
            return False, "Ошибка проверки номера телефона"
    
    async def change_phone_number(
        self,
        user: User,
        new_phone: str
    ) -> None:
        """Изменяет номер телефона пользователя."""
        try:
            # Валидируем новый номер
            validation_result = PhoneValidator.validate_phone(new_phone)
            if not validation_result.is_valid:
                raise ValidationError(
                    f"Некорректный номер телефона: {', '.join(validation_result.errors)}",
                    field="phone",
                    value=new_phone
                )
            
            # Проверяем, не занят ли номер
            existing_user = await self.user_repo.get_by_phone(validation_result.normalized_value)
            if existing_user and existing_user.id != user.id:
                raise ValidationError(
                    "Номер телефона уже используется другим пользователем",
                    field="phone",
                    value=new_phone
                )
            
            old_phone_hash = hash_phone_number(user.phone or "")
            new_phone_hash = hash_phone_number(validation_result.normalized_value)
            
            await self.user_repo.update_phone(user, validation_result.normalized_value)
            
            logger.info(
                f"Изменен номер телефона для пользователя {user.id}: "
                f"{old_phone_hash} -> {new_phone_hash}"
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Ошибка изменения номера телефона для пользователя {user.id}: {e}")
            raise DatabaseError(f"Ошибка изменения номера телефона: {e}")
    
    async def verify_telegram_account(self, user: User) -> None:
        """Помечает аккаунт пользователя как верифицированный через Telegram."""
        try:
            await self.user_repo.verify_telegram(user)
            logger.info(f"Пользователь {user.id} верифицирован через Telegram")
        except Exception as e:
            logger.error(f"Ошибка верификации через Telegram для пользователя {user.id}: {e}")
            raise DatabaseError(f"Ошибка верификации: {e}")
    
    async def get_display_name(self, user: User) -> str:
        """Получает отображаемое имя пользователя."""
        try:
            return await self.user_repo.get_user_display_name(user)
        except Exception as e:
            logger.error(f"Ошибка получения отображаемого имени для пользователя {user.id}: {e}")
            return "Пользователь"
    
    async def check_user_exists_by_phone(self, phone: str) -> bool:
        """Проверяет, существует ли пользователь с указанным номером телефона."""
        try:
            validation_result = PhoneValidator.validate_phone(phone)
            if not validation_result.is_valid:
                return False
            
            return await self.user_repo.phone_exists(validation_result.normalized_value)
        except Exception as e:
            phone_hash = hash_phone_number(phone)
            logger.error(f"Ошибка проверки существования пользователя по телефону {phone_hash}: {e}")
            return False
    
    async def check_user_exists_by_chat_id(self, chat_id: str) -> bool:
        """Проверяет, существует ли пользователь с указанным chat_id."""
        try:
            return await self.user_repo.chat_id_exists(chat_id)
        except Exception as e:
            logger.error(f"Ошибка проверки существования пользователя по chat_id {chat_id}: {e}")
            return False
    
    async def get_user_stats(self) -> dict:
        """Получает статистику по пользователям."""
        try:
            # Здесь можно добавить логику для получения статистики
            # Пока возвращаем базовую информацию
            return {
                'service': 'user_service',
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователей: {e}")
            return {}