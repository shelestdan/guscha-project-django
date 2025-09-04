"""Сервис верификации для Telegram бота."""

import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone

from apps.accounts.models import TelegramVerificationCode, User, PendingUserRegistration
from ..repositories import VerificationCodeRepository, QRCodeRepository
from ..exceptions import VerificationCodeError, RateLimitError
from ..config.settings import bot_settings
from ..utils.validators import PhoneValidator, ValidationResult
from ..utils.helpers import generate_secure_code

logger = logging.getLogger(__name__)


class VerificationService:
    """Сервис для работы с верификацией."""
    
    def __init__(self):
        self.verification_repo = VerificationCodeRepository()
        self.qr_repo = QRCodeRepository()
    
    async def find_verification_code(
        self,
        chat_id: str,
        verification_id: Optional[str] = None,
        is_login: bool = False
    ) -> Optional[TelegramVerificationCode]:
        """Находит код верификации по различным критериям."""
        try:
            verification_code = None
            
            # Если передан verification_id, ищем по нему
            if verification_id:
                logger.info(f"Поиск verification_code для ID: {verification_id}, is_login: {is_login}")
                
                # Сначала пытаемся найти QR-код по qr_id (только если это не login)
                if not is_login:
                    qr_code = await self.qr_repo.get_by_qr_id(verification_id)
                    if qr_code and qr_code.verification_code:
                        verification_code = qr_code.verification_code
                        logger.info(f"Найден QR-код: {qr_code.qr_id}")
                
                # Если QR-код не найден, ищем обычным способом
                if not verification_code:
                    if is_login:
                        # Для login ищем среди активных кодов входа
                        logger.info(f"Поиск login кода среди активных кодов")
                        active_login_codes = await self.verification_repo.get_active_login_codes()
                        for code in active_login_codes:
                            if await self.verification_repo.check_code_match(code, verification_id):
                                verification_code = code
                                logger.info(f"Найден login код: {code.id}")
                                break
                    else:
                        # Для register параметров сначала пытаемся найти по ID записи
                        logger.info(f"Поиск кода верификации по ID записи: {verification_id}")
                        verification_code = await self.verification_repo.get_by_id(verification_id)
                        
                        if verification_code:
                            logger.info(f"Найден код по ID записи: {verification_code.id}, тип: {verification_code.verification_type}")
                        else:
                            # Если не найден по ID, пытаемся найти по коду
                            logger.info(f"Код не найден по ID, ищем по коду: {verification_id}")
                            verification_code = await self.verification_repo.get_by_code(verification_id)
                            if verification_code:
                                logger.info(f"Найден код по коду: {verification_code.id}, тип: {verification_code.verification_type}")
            
            # Если не найден по ID, ищем по chat_id
            if not verification_code:
                logger.info(f"Код не найден по ID, ищем по chat_id: {chat_id}")
                verification_code = await self.verification_repo.get_by_chat_id(chat_id)
                if verification_code:
                    logger.info(f"Найден код по chat_id: {verification_code.id}, тип: {verification_code.verification_type}")
            
            # Проверяем активность кода
            if verification_code and await self.verification_repo.is_expired(verification_code):
                logger.warning(f"Код верификации {verification_code.id} истек")
                return None
            
            if verification_code:
                logger.info(f"Итоговый найденный код: {verification_code.id}, chat_id: {verification_code.telegram_chat_id}, тип: {verification_code.verification_type}")
            else:
                logger.warning(f"Код верификации не найден для ID: {verification_id}, chat_id: {chat_id}")
            
            return verification_code
            
        except Exception as e:
            logger.error(f"Ошибка при поиске кода верификации: {e}")
            raise VerificationCodeError(f"Ошибка поиска кода верификации: {e}")
    
    async def create_verification_code(
        self,
        verification_type: str,
        chat_id: Optional[str] = None,
        user: Optional[User] = None,
        pending_registration: Optional[PendingUserRegistration] = None,
        telegram_phone: Optional[str] = None
    ) -> TelegramVerificationCode:
        """Создает новый код верификации."""
        try:
            return await self.verification_repo.create(
                verification_type=verification_type,
                chat_id=chat_id,
                user=user,
                pending_registration=pending_registration,
                telegram_phone=telegram_phone,
                expires_in_minutes=bot_settings.verification_code_timeout_minutes
            )
        except Exception as e:
            logger.error(f"Ошибка создания кода верификации: {e}")
            raise VerificationCodeError(f"Ошибка создания кода верификации: {e}")
    
    async def update_verification_code(
        self,
        verification_code: TelegramVerificationCode,
        chat_id: Optional[str] = None,
        phone: Optional[str] = None
    ) -> TelegramVerificationCode:
        """Обновляет код верификации с chat_id и/или номером телефона."""
        try:
            logger.info(f"Обновление кода верификации {verification_code.id}")
            if chat_id:
                logger.info(f"Обновление chat_id с {verification_code.telegram_chat_id} на {chat_id}")
            if phone:
                logger.info(f"Обновление номера телефона на {phone}")
            
            updated_code = verification_code
            
            # Обновляем chat_id если передан
            if chat_id:
                updated_code = await self.verification_repo.update_chat_id(
                    updated_code, 
                    chat_id
                )
            
            # Обновляем номер телефона если передан
            if phone:
                updated_code = await self.verification_repo.update_phone(
                    updated_code,
                    phone
                )
            
            logger.info(f"Код верификации {verification_code.id} успешно обновлен")
            return updated_code
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении кода верификации {verification_code.id}: {e}")
            raise VerificationCodeError(f"Ошибка обновления кода верификации: {e}")
    
    async def verify_phone_match(
        self,
        verification_code: TelegramVerificationCode,
        telegram_phone: str
    ) -> Tuple[bool, Optional[str]]:
        """Проверяет совпадение номера телефона с зарегистрированным."""
        try:
            # Получаем зарегистрированный номер
            registered_phone = ""
            
            if verification_code.user:
                registered_phone = verification_code.user.phone or ""
            elif verification_code.pending_registration:
                registered_phone = verification_code.pending_registration.phone or ""
            
            if not registered_phone:
                return False, "В регистрации не указан номер телефона"
            
            # Проверяем совпадение номеров
            validation_result = PhoneValidator.validate_phone_match(telegram_phone, registered_phone)
            
            if validation_result.is_valid:
                return True, None
            else:
                return False, ", ".join(validation_result.errors)
                
        except Exception as e:
            logger.error(f"Ошибка проверки совпадения номеров: {e}")
            return False, "Ошибка проверки номера телефона"
    
    async def generate_display_code(self, verification_code: TelegramVerificationCode) -> str:
        """Генерирует код для отображения пользователю."""
        try:
            return await self.verification_repo.generate_secure_code(verification_code)
        except Exception as e:
            logger.error(f"Ошибка генерации кода для отображения: {e}")
            raise VerificationCodeError(f"Ошибка генерации кода: {e}")
    
    async def is_expired(self, verification_code: TelegramVerificationCode) -> bool:
        """Проверяет, истек ли код верификации."""
        try:
            return await self.verification_repo.is_expired(verification_code)
        except Exception as e:
            logger.error(f"Ошибка проверки истечения кода верификации: {e}")
            raise VerificationCodeError(f"Ошибка проверки истечения кода: {e}")
    
    async def mark_as_used(self, verification_code: TelegramVerificationCode) -> None:
        """Помечает код верификации как использованный."""
        try:
            await self.verification_repo.mark_as_used(verification_code)
        except Exception as e:
            logger.error(f"Ошибка пометки кода как использованного: {e}")
            raise VerificationCodeError(f"Ошибка использования кода: {e}")
    
    async def verify_code(
        self,
        verification_code: TelegramVerificationCode,
        code: str
    ) -> bool:
        """Верифицирует код и помечает как использованный."""
        try:
            return await self.verification_repo.verify_code(verification_code, code)
        except Exception as e:
            logger.error(f"Ошибка верификации кода: {e}")
            raise VerificationCodeError(f"Ошибка верификации кода: {e}")
    
    async def check_code_match(
        self,
        verification_code: TelegramVerificationCode,
        code: str
    ) -> bool:
        """Проверяет соответствие кода без его использования."""
        try:
            return await self.verification_repo.check_code_match(verification_code, code)
        except Exception as e:
            logger.error(f"Ошибка проверки соответствия кода: {e}")
            return False
    
    async def handle_qr_code_verification(
        self,
        verification_code: TelegramVerificationCode,
        display_code: str
    ) -> None:
        """Обрабатывает верификацию QR-кода."""
        try:
            # Отмечаем запуск бота для QR-кода
            qr_code = await self.qr_repo.find_matching_qr_code(display_code)
            if qr_code:
                await self.qr_repo.mark_bot_started(qr_code)
                logger.info(f"Запуск бота отмечен для QR-кода {qr_code.qr_id}")
        except Exception as e:
            logger.error(f"Ошибка обработки QR-кода: {e}")
            # Не прерываем процесс, если не удалось отметить QR-код
    
    async def get_verification_type_display(self, verification_type: str) -> str:
        """Возвращает отображаемое название типа верификации."""
        type_mapping = {
            'registration': 'регистрации',
            'login': 'входа',
            'qr_registration': 'QR-регистрации',
            'telegram_registration': 'регистрации через Telegram',
            'phone_change_current': 'подтверждения текущего номера',
            'phone_change_new': 'смены номера телефона',
        }
        return type_mapping.get(verification_type, verification_type)
    
    async def cleanup_expired_codes(self) -> int:
        """Очищает истекшие коды верификации."""
        try:
            count = await self.verification_repo.cleanup_expired_codes()
            logger.info(f"Очищено {count} истекших кодов верификации")
            return count
        except Exception as e:
            logger.error(f"Ошибка очистки истекших кодов: {e}")
            return 0
    
    async def get_verification_stats(self) -> dict:
        """Получает статистику по кодам верификации."""
        try:
            # Здесь можно добавить логику для получения статистики
            # Пока возвращаем базовую информацию
            return {
                'cleanup_performed': True,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики верификации: {e}")
            return {}