"""Репозиторий для работы с пользователями."""

from typing import Optional
from asgiref.sync import sync_to_async

from apps.accounts.models import User
from ..exceptions import DatabaseError, UserNotFoundError
from ..utils.validators import PhoneValidator
from ..utils.database_pool import async_db_operation, async_db_transaction, async_db_monitored


class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    @staticmethod
    @async_db_monitored()
    async def get_by_id(user_id: int) -> Optional[User]:
        """Получает пользователя по ID."""
        try:
            return await sync_to_async(
                User.objects.filter(id=user_id).first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения пользователя по ID: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def get_by_phone(phone: str) -> Optional[User]:
        """Получает пользователя по номеру телефона."""
        try:
            # Нормализуем номер телефона
            normalized_phone = PhoneValidator.normalize_phone(phone)
            
            return await sync_to_async(
                User.objects.filter(phone=normalized_phone).first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения пользователя по телефону: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def get_by_chat_id(chat_id: str) -> Optional[User]:
        """Получает пользователя по Telegram chat_id."""
        try:
            return await sync_to_async(
                User.objects.filter(telegram_chat_id=chat_id).first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения пользователя по chat_id: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def get_by_email(email: str) -> Optional[User]:
        """Получает пользователя по email."""
        try:
            return await sync_to_async(
                User.objects.filter(email=email).first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения пользователя по email: {e}")
    
    @staticmethod
    @async_db_transaction()
    async def create_telegram_user(
        phone: str,
        chat_id: str,
        telegram_username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Создает пользователя через Telegram регистрацию."""
        try:
            # Валидируем номер телефона
            validation_result = PhoneValidator.validate_phone(phone)
            if not validation_result.is_valid:
                raise ValueError(f"Некорректный номер телефона: {', '.join(validation_result.errors)}")
            
            normalized_phone = validation_result.normalized_value
            
            # Проверяем, не существует ли уже пользователь с таким номером
            existing_user = await UserRepository.get_by_phone(normalized_phone)
            if existing_user:
                raise ValueError("Пользователь с таким номером телефона уже существует")
            
            # Проверяем, не привязан ли уже этот chat_id к другому пользователю
            existing_chat_user = await UserRepository.get_by_chat_id(chat_id)
            if existing_chat_user:
                raise ValueError("Этот Telegram аккаунт уже привязан к другому пользователю")
            
            # Генерируем временный email на основе номера телефона
            clean_phone = normalized_phone.replace('+', '').replace(' ', '').replace('-', '')
            temp_email = f"telegram_{clean_phone}@temp.local"
            
            # Проверяем уникальность email
            email_exists = await sync_to_async(
                User.objects.filter(email=temp_email).exists
            )()
            if email_exists:
                # Добавляем timestamp для уникальности
                import time
                temp_email = f"telegram_{clean_phone}_{int(time.time())}@temp.local"
            
            # Генерируем случайный пароль
            import secrets
            import string
            temp_password = ''.join(
                secrets.choice(string.ascii_letters + string.digits + '@$!%*?&') 
                for _ in range(12)
            )
            
            # Создаем пользователя
            user = await sync_to_async(User.objects.create_user)(
                email=temp_email,
                password=temp_password,
                phone=normalized_phone,
                telegram_chat_id=chat_id,
                telegram_username=telegram_username or '',
                is_telegram_verified=True,
                is_active=True,
                first_name=first_name or '',
                last_name=last_name or ''
            )
            
            return user
            
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise DatabaseError(f"Ошибка создания пользователя через Telegram: {e}")
    
    @async_db_transaction()
    async def update_telegram_info(
        self,
        user: User,
        chat_id: str,
        username: Optional[str] = None
    ) -> None:
        """Обновляет Telegram информацию пользователя."""
        try:
            user.telegram_chat_id = chat_id
            if username:
                user.telegram_username = username
            await sync_to_async(user.save)()
        except Exception as e:
            raise DatabaseError(f"Ошибка обновления Telegram информации: {e}")
    
    @async_db_transaction()
    async def update_phone(
        self,
        user: User,
        new_phone: str
    ) -> None:
        """Обновляет номер телефона пользователя."""
        try:
            # Валидируем новый номер
            validation_result = PhoneValidator.validate_phone(new_phone)
            if not validation_result.is_valid:
                raise ValueError(f"Некорректный номер телефона: {', '.join(validation_result.errors)}")
            
            normalized_phone = validation_result.normalized_value
            
            # Проверяем, не занят ли номер другим пользователем
            existing_user = await self.get_by_phone(normalized_phone)
            if existing_user and existing_user.id != user.id:
                raise ValueError("Номер телефона уже используется другим пользователем")
            
            user.phone = normalized_phone
            await sync_to_async(user.save)()
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise DatabaseError(f"Ошибка обновления номера телефона: {e}")
    
    @async_db_transaction()
    async def verify_telegram(
        self,
        user: User
    ) -> None:
        """Помечает пользователя как верифицированного через Telegram."""
        try:
            user.is_telegram_verified = True
            await sync_to_async(user.save)()
        except Exception as e:
            raise DatabaseError(f"Ошибка верификации через Telegram: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def phone_exists(phone: str) -> bool:
        """Проверяет, существует ли пользователь с таким номером телефона."""
        try:
            normalized_phone = PhoneValidator.normalize_phone(phone)
            return await sync_to_async(
                User.objects.filter(phone=normalized_phone).exists
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки существования номера телефона: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def chat_id_exists(chat_id: str) -> bool:
        """Проверяет, существует ли пользователь с таким chat_id."""
        try:
            return await sync_to_async(
                User.objects.filter(telegram_chat_id=chat_id).exists
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки существования chat_id: {e}")
    
    @staticmethod
    @async_db_monitored()
    async def email_exists(email: str) -> bool:
        """Проверяет, существует ли пользователь с таким email."""
        try:
            return await sync_to_async(
                User.objects.filter(email=email).exists
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки существования email: {e}")
    
    @staticmethod
    async def get_user_display_name(user: User) -> str:
        """Получает отображаемое имя пользователя."""
        try:
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.telegram_username:
                return f"@{user.telegram_username}"
            else:
                return "Пользователь"
        except Exception as e:
            raise DatabaseError(f"Ошибка получения отображаемого имени: {e}")