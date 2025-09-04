"""Сервис для контроля частоты запросов (rate limiting)."""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache

from ..repositories import VerificationCodeRepository
from ..exceptions import RateLimitError
from ..config.settings import bot_settings
from ..utils.helpers import rate_limit_key

logger = logging.getLogger(__name__)


class RateLimitService:
    """Сервис для контроля частоты запросов."""
    
    def __init__(self):
        self.verification_repo = VerificationCodeRepository()
    
    async def check_registration_rate_limit(self, chat_id: str) -> bool:
        """Проверяет лимит регистрации для chat_id."""
        try:
            # Проверяем количество попыток регистрации за последние N минут
            count = await self.verification_repo.count_recent_attempts(
                chat_id=chat_id,
                verification_type='telegram_registration',
                minutes=bot_settings.registration_rate_limit_minutes
            )
            
            is_allowed = count < bot_settings.max_registration_attempts
            
            if not is_allowed:
                logger.warning(
                    f"Превышен лимит регистрации для chat_id {chat_id}: "
                    f"{count}/{bot_settings.max_registration_attempts} за "
                    f"{bot_settings.registration_rate_limit_minutes} минут"
                )
            
            return is_allowed
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимита регистрации для chat_id {chat_id}: {e}")
            # В случае ошибки разрешаем продолжить
            return True
    
    def check_phone_validation_rate_limit(self, chat_id: str) -> bool:
        """Проверяет лимит валидации номера телефона."""
        try:
            key = rate_limit_key(chat_id, 'phone_validation')
            
            # Получаем текущее количество попыток
            current_attempts = cache.get(key, 0)
            
            if current_attempts >= bot_settings.max_phone_validation_attempts:
                logger.warning(
                    f"Превышен лимит валидации телефона для chat_id {chat_id}: "
                    f"{current_attempts}/{bot_settings.max_phone_validation_attempts}"
                )
                return False
            
            # Увеличиваем счетчик
            cache.set(
                key, 
                current_attempts + 1, 
                timeout=bot_settings.phone_validation_timeout_minutes * 60
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимита валидации телефона для chat_id {chat_id}: {e}")
            # В случае ошибки разрешаем продолжить
            return True
    
    def check_message_rate_limit(self, chat_id: str, action: str = 'message') -> bool:
        """Проверяет общий лимит сообщений."""
        try:
            key = rate_limit_key(chat_id, action)
            
            # Простой rate limiting: не более 10 сообщений в минуту
            max_messages = 10
            timeout_minutes = 1
            
            current_count = cache.get(key, 0)
            
            if current_count >= max_messages:
                logger.warning(
                    f"Превышен лимит сообщений для chat_id {chat_id}, действие {action}: "
                    f"{current_count}/{max_messages} за {timeout_minutes} минут"
                )
                return False
            
            # Увеличиваем счетчик
            cache.set(key, current_count + 1, timeout=timeout_minutes * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки лимита сообщений для chat_id {chat_id}: {e}")
            # В случае ошибки разрешаем продолжить
            return True
    
    def get_rate_limit_info(self, chat_id: str, action: str) -> Dict[str, any]:
        """Получает информацию о текущих лимитах для пользователя."""
        try:
            key = rate_limit_key(chat_id, action)
            current_count = cache.get(key, 0)
            
            # Определяем лимиты в зависимости от действия
            if action == 'phone_validation':
                max_attempts = bot_settings.max_phone_validation_attempts
                timeout_minutes = bot_settings.phone_validation_timeout_minutes
            elif action == 'message':
                max_attempts = 10
                timeout_minutes = 1
            else:
                max_attempts = 5
                timeout_minutes = 5
            
            return {
                'action': action,
                'current_count': current_count,
                'max_attempts': max_attempts,
                'timeout_minutes': timeout_minutes,
                'remaining': max(0, max_attempts - current_count),
                'is_limited': current_count >= max_attempts
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о лимитах для chat_id {chat_id}: {e}")
            return {
                'action': action,
                'error': str(e)
            }
    
    def reset_rate_limit(self, chat_id: str, action: str) -> bool:
        """Сбрасывает лимит для пользователя (для административных целей)."""
        try:
            key = rate_limit_key(chat_id, action)
            cache.delete(key)
            logger.info(f"Сброшен лимит для chat_id {chat_id}, действие {action}")
            return True
        except Exception as e:
            logger.error(f"Ошибка сброса лимита для chat_id {chat_id}: {e}")
            return False
    
    async def check_verification_code_rate_limit(
        self, 
        chat_id: str, 
        verification_type: str
    ) -> bool:
        """Проверяет лимит создания кодов верификации."""
        try:
            # Определяем лимиты в зависимости от типа верификации
            if verification_type == 'telegram_registration':
                return await self.check_registration_rate_limit(chat_id)
            elif verification_type in ['login', 'phone_change_current', 'phone_change_new']:
                # Для входа и смены телефона - более строгие лимиты
                count = await self.verification_repo.count_recent_attempts(
                    chat_id=chat_id,
                    verification_type=verification_type,
                    minutes=5
                )
                return count < 3
            else:
                # Для остальных типов - стандартные лимиты
                count = await self.verification_repo.count_recent_attempts(
                    chat_id=chat_id,
                    verification_type=verification_type,
                    minutes=10
                )
                return count < 5
                
        except Exception as e:
            logger.error(
                f"Ошибка проверки лимита кодов верификации для chat_id {chat_id}, "
                f"тип {verification_type}: {e}"
            )
            # В случае ошибки разрешаем продолжить
            return True
    
    def raise_rate_limit_error(
        self, 
        action: str, 
        retry_after_minutes: int,
        context: Optional[str] = None
    ) -> None:
        """Вызывает исключение о превышении лимита."""
        message = f"Превышен лимит для действия '{action}'. Попробуйте через {retry_after_minutes} минут."
        if context:
            message += f" Контекст: {context}"
        
        raise RateLimitError(
            message=message,
            retry_after_seconds=retry_after_minutes * 60,
            error_code="RATE_LIMIT_EXCEEDED",
            context={'action': action, 'retry_after_minutes': retry_after_minutes}
        )
    
    def get_all_rate_limits(self, chat_id: str) -> Dict[str, any]:
        """Получает информацию обо всех лимитах для пользователя."""
        try:
            actions = ['phone_validation', 'message', 'registration']
            limits = {}
            
            for action in actions:
                limits[action] = self.get_rate_limit_info(chat_id, action)
            
            return {
                'chat_id': chat_id,
                'limits': limits,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения всех лимитов для chat_id {chat_id}: {e}")
            return {
                'chat_id': chat_id,
                'error': str(e)
            }