"""Репозиторий для работы с кодами верификации."""

from typing import Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

from apps.accounts.models import TelegramVerificationCode, User, PendingUserRegistration
from ..exceptions import DatabaseError, VerificationCodeError
from ..utils.validators import ValidationResult


class VerificationCodeRepository:
    """Репозиторий для работы с кодами верификации Telegram."""
    
    @staticmethod
    async def get_by_id(verification_id: str) -> Optional[TelegramVerificationCode]:
        """Получает код верификации по ID."""
        try:
            # Проверяем, является ли ID числовым (обычный ID записи)
            if verification_id.isdigit():
                return await sync_to_async(
                    TelegramVerificationCode.objects.filter(
                        id=int(verification_id)
                    ).select_related('user', 'pending_registration').first
                )()
            else:
                # Если ID не числовой, возвращаем None
                # UUID должны обрабатываться через QRCodeRepository
                return None
        except Exception as e:
            raise DatabaseError(f"Ошибка получения кода верификации по ID: {e}")
    
    @staticmethod
    async def get_by_code(code: str) -> Optional[TelegramVerificationCode]:
        """Получает код верификации по коду."""
        try:
            return await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    code=code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).select_related('user', 'pending_registration').first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения кода верификации по коду: {e}")
    
    @staticmethod
    async def get_by_chat_id(
        chat_id: str, 
        verification_type: Optional[str] = None,
        only_active: bool = True
    ) -> Optional[TelegramVerificationCode]:
        """Получает код верификации по chat_id."""
        try:
            queryset = TelegramVerificationCode.objects.filter(
                telegram_chat_id=chat_id
            ).select_related('user', 'pending_registration')
            
            if verification_type:
                queryset = queryset.filter(verification_type=verification_type)
            
            if only_active:
                queryset = queryset.filter(
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
            
            return await sync_to_async(
                queryset.order_by('-created_at').first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения кода верификации по chat_id: {e}")
    
    @staticmethod
    async def get_by_user(
        user: User,
        verification_type: Optional[str] = None,
        only_active: bool = True
    ) -> Optional[TelegramVerificationCode]:
        """Получает код верификации по пользователю."""
        try:
            queryset = TelegramVerificationCode.objects.filter(
                user=user
            ).select_related('user', 'pending_registration')
            
            if verification_type:
                queryset = queryset.filter(verification_type=verification_type)
            
            if only_active:
                queryset = queryset.filter(
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
            
            return await sync_to_async(
                queryset.order_by('-created_at').first
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка получения кода верификации по пользователю: {e}")
    
    @staticmethod
    async def get_active_login_codes() -> List[TelegramVerificationCode]:
        """Получает все активные коды входа."""
        try:
            return await sync_to_async(
                list
            )(
                TelegramVerificationCode.objects.filter(
                    verification_type='login',
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).select_related('user', 'pending_registration').order_by('-created_at')
            )
        except Exception as e:
            raise DatabaseError(f"Ошибка получения активных кодов входа: {e}")
    
    @staticmethod
    async def create(
        verification_type: str,
        chat_id: Optional[str] = None,
        user: Optional[User] = None,
        pending_registration: Optional[PendingUserRegistration] = None,
        telegram_phone: Optional[str] = None,
        expires_in_minutes: int = 10
    ) -> TelegramVerificationCode:
        """Создает новый код верификации."""
        try:
            expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)
            
            verification_code = await sync_to_async(
                TelegramVerificationCode.objects.create
            )(
                verification_type=verification_type,
                telegram_chat_id=chat_id,
                user=user,
                pending_registration=pending_registration,
                telegram_phone=telegram_phone,
                expires_at=expires_at
            )
            
            return verification_code
        except Exception as e:
            raise DatabaseError(f"Ошибка создания кода верификации: {e}")
    
    @staticmethod
    async def update_chat_id(
        verification_code: TelegramVerificationCode,
        chat_id: str
    ) -> TelegramVerificationCode:
        """Обновляет chat_id для кода верификации."""
        try:
            verification_code.telegram_chat_id = chat_id
            await sync_to_async(verification_code.save)()
            return verification_code
        except Exception as e:
            raise DatabaseError(f"Ошибка обновления chat_id: {e}")
    
    @staticmethod
    async def update_phone(
        verification_code: TelegramVerificationCode,
        phone: str
    ) -> TelegramVerificationCode:
        """Обновляет номер телефона для кода верификации."""
        try:
            verification_code.telegram_phone = phone
            await sync_to_async(verification_code.save)()
            return verification_code
        except Exception as e:
            raise DatabaseError(f"Ошибка обновления номера телефона: {e}")
    
    @staticmethod
    async def mark_as_used(verification_code: TelegramVerificationCode) -> None:
        """Помечает код верификации как использованный."""
        try:
            verification_code.is_used = True
            await sync_to_async(verification_code.save)()
        except Exception as e:
            raise DatabaseError(f"Ошибка пометки кода как использованного: {e}")
    
    @staticmethod
    async def link_user(
        verification_code: TelegramVerificationCode,
        user: User
    ) -> None:
        """Связывает код верификации с пользователем."""
        try:
            verification_code.user = user
            await sync_to_async(verification_code.save)()
        except Exception as e:
            raise DatabaseError(f"Ошибка связывания кода с пользователем: {e}")
    
    @staticmethod
    async def check_code_match(
        verification_code: TelegramVerificationCode,
        code: str
    ) -> bool:
        """Проверяет соответствие кода без его использования."""
        try:
            return await sync_to_async(verification_code.check_code_match)(code)
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки соответствия кода: {e}")
    
    @staticmethod
    async def verify_code(
        verification_code: TelegramVerificationCode,
        code: str
    ) -> bool:
        """Верифицирует код и помечает как использованный."""
        try:
            return await sync_to_async(verification_code.verify_code)(code)
        except Exception as e:
            raise DatabaseError(f"Ошибка верификации кода: {e}")
    
    @staticmethod
    async def generate_secure_code(verification_code: TelegramVerificationCode) -> str:
        """Генерирует безопасный код для отображения."""
        try:
            return await sync_to_async(verification_code.generate_secure_code)()
        except Exception as e:
            raise DatabaseError(f"Ошибка генерации безопасного кода: {e}")
    
    @staticmethod
    async def is_expired(verification_code: TelegramVerificationCode) -> bool:
        """Проверяет, истек ли код верификации."""
        try:
            return await sync_to_async(verification_code.is_expired)()
        except Exception as e:
            raise DatabaseError(f"Ошибка проверки истечения кода: {e}")
    
    @staticmethod
    async def count_recent_attempts(
        chat_id: str,
        verification_type: str,
        minutes: int = 5
    ) -> int:
        """Подсчитывает количество недавних попыток."""
        try:
            since = timezone.now() - timedelta(minutes=minutes)
            return await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=chat_id,
                    verification_type=verification_type,
                    created_at__gte=since
                ).count
            )()
        except Exception as e:
            raise DatabaseError(f"Ошибка подсчета недавних попыток: {e}")
    
    @staticmethod
    async def cleanup_expired_codes() -> int:
        """Удаляет истекшие коды верификации."""
        try:
            expired_codes = TelegramVerificationCode.objects.filter(
                expires_at__lt=timezone.now()
            )
            count = await sync_to_async(expired_codes.count)()
            await sync_to_async(expired_codes.delete)()
            return count
        except Exception as e:
            raise DatabaseError(f"Ошибка очистки истекших кодов: {e}")