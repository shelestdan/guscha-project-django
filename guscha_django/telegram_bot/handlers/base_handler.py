"""Базовый класс для обработчиков Telegram бота."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from ..services import (
    VerificationService,
    UserService,
    PhoneService,
    RateLimitService,
    MessageService
)
from ..exceptions import TelegramBotError, RateLimitError
from ..utils.helpers import get_user_display_name

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков команд."""
    
    def __init__(
        self,
        verification_service: VerificationService,
        user_service: UserService,
        phone_service: PhoneService,
        rate_limit_service: RateLimitService,
        message_service: MessageService
    ):
        self.verification_service = verification_service
        self.user_service = user_service
        self.phone_service = phone_service
        self.rate_limit_service = rate_limit_service
        self.message_service = message_service
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
        error_context: Optional[str] = None
    ) -> None:
        """Обрабатывает ошибки в обработчиках."""
        try:
            chat_id = str(update.effective_chat.id)
            user = update.effective_user
            
            # Логируем ошибку
            error_msg = f"Ошибка в {self.__class__.__name__}"
            if error_context:
                error_msg += f" ({error_context})"
            error_msg += f": {error}"
            
            self.logger.error(
                error_msg,
                extra={
                    'chat_id': chat_id,
                    'user_id': user.id if user else None,
                    'username': user.username if user else None,
                    'error_type': type(error).__name__
                },
                exc_info=True
            )
            
            # Отправляем пользователю сообщение об ошибке
            if isinstance(error, RateLimitError):
                await self.message_service.send_error_message(
                    chat_id=chat_id,
                    error_type='rate_limit',
                    minutes=error.retry_after_seconds // 60
                )
            elif isinstance(error, TelegramBotError):
                # Для кастомных ошибок бота отправляем специфичное сообщение
                await self.message_service.send_simple_message(
                    chat_id=chat_id,
                    text=f"❌ {error.message}"
                )
            else:
                # Для всех остальных ошибок - общее сообщение
                await self.message_service.send_error_message(
                    chat_id=chat_id,
                    error_type='general'
                )
                
        except Exception as e:
            # Если не удалось обработать ошибку, логируем это
            self.logger.critical(
                f"Критическая ошибка при обработке ошибки в {self.__class__.__name__}: {e}",
                exc_info=True
            )
    
    def get_user_info(self, update: Update) -> Dict[str, Any]:
        """Извлекает информацию о пользователе из update."""
        user = update.effective_user
        chat = update.effective_chat
        
        return {
            'user_id': user.id if user else None,
            'chat_id': str(chat.id) if chat else None,
            'username': user.username if user else None,
            'first_name': user.first_name if user else None,
            'last_name': user.last_name if user else None,
            'display_name': get_user_display_name(
                user.first_name if user else None,
                user.last_name if user else None,
                user.username if user else None
            )
        }
    
    async def check_rate_limit(
        self,
        chat_id: str,
        action: str,
        raise_on_limit: bool = True
    ) -> bool:
        """Проверяет лимит частоты запросов."""
        try:
            is_allowed = self.rate_limit_service.check_message_rate_limit(chat_id, action)
            
            if not is_allowed and raise_on_limit:
                self.rate_limit_service.raise_rate_limit_error(
                    action=action,
                    retry_after_minutes=1,
                    context=f"Handler: {self.__class__.__name__}"
                )
            
            return is_allowed
            
        except RateLimitError:
            raise
        except Exception as e:
            self.logger.error(f"Ошибка проверки rate limit для {action}: {e}")
            # В случае ошибки разрешаем продолжить
            return True
    
    def log_handler_start(
        self,
        handler_name: str,
        user_info: Dict[str, Any],
        additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логирует начало обработки команды."""
        log_data = {
            'handler': handler_name,
            'chat_id': user_info.get('chat_id'),
            'user_id': user_info.get('user_id'),
            'username': user_info.get('username'),
        }
        
        if additional_info:
            log_data.update(additional_info)
        
        self.logger.info(
            f"Начало обработки {handler_name} для пользователя {user_info.get('display_name')}",
            extra=log_data
        )
    
    def log_handler_success(
        self,
        handler_name: str,
        user_info: Dict[str, Any],
        result_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Логирует успешное завершение обработки."""
        log_data = {
            'handler': handler_name,
            'chat_id': user_info.get('chat_id'),
            'user_id': user_info.get('user_id'),
            'status': 'success'
        }
        
        if result_info:
            log_data.update(result_info)
        
        self.logger.info(
            f"Успешное завершение {handler_name} для пользователя {user_info.get('display_name')}",
            extra=log_data
        )
    

    
    async def _find_comprehensive_verification_code(self, identifier: str) -> Optional[object]:
        """Находит активный код верификации по chat_id или verification_id.
        
        Args:
            identifier: chat_id или verification_id для поиска
            
        Returns:
            TelegramVerificationCode или None если не найден
        """
        try:
            # Определяем, является ли identifier chat_id (обычно числовой)
            # или verification_id (может быть строкой или числом)
            
            # Сначала пытаемся найти по chat_id
            verification_code = await self.verification_service.find_verification_code(
                chat_id=identifier,
                verification_id=None,
                is_login=False
            )
            
            # Если не найден по chat_id, пытаемся найти по verification_id
            if not verification_code:
                verification_code = await self.verification_service.find_verification_code(
                    chat_id="",  # Пустой chat_id для поиска только по ID
                    verification_id=identifier,
                    is_login=False
                )
            
            return verification_code
            
        except Exception as e:
            self.logger.error(f"Ошибка при поиске кода верификации для {identifier}: {e}")
            return None

    @abstractmethod
    async def handle(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Абстрактный метод для обработки запроса."""
        pass
    
    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Вызов обработчика с обработкой ошибок."""
        try:
            await self.handle(update, context)
        except Exception as e:
            await self.handle_error(update, context, e)


class CommandHandler(BaseHandler):
    """Базовый класс для обработчиков команд."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def extract_command_args(self, context: ContextTypes.DEFAULT_TYPE) -> list:
        """Извлекает аргументы команды."""
        return context.args or []
    
    def get_command_parameter(self, context: ContextTypes.DEFAULT_TYPE, index: int = 0) -> Optional[str]:
        """Получает параметр команды по индексу."""
        args = self.extract_command_args(context)
        return args[index] if len(args) > index else None


class CallbackQueryHandler(BaseHandler):
    """Базовый класс для обработчиков callback запросов."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def parse_callback_data(self, callback_data: str) -> tuple[str, Optional[str]]:
        """Парсит callback_data на действие и параметр."""
        if '_' in callback_data:
            action, param = callback_data.split('_', 1)
            return action, param
        return callback_data, None
    
    async def answer_callback_query(
        self,
        update: Update,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> None:
        """Отвечает на callback query."""
        try:
            query = update.callback_query
            if query:
                await query.answer(text=text, show_alert=show_alert)
        except Exception as e:
            self.logger.error(f"Ошибка ответа на callback query: {e}")
    
class MessageHandler(BaseHandler):
    """Базовый класс для обработчиков сообщений."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_message_text(self, update: Update) -> Optional[str]:
        """Получает текст сообщения."""
        message = update.message
        return message.text if message else None
    
    def get_contact(self, update: Update):
        """Получает контакт из сообщения."""
        message = update.message
        return message.contact if message else None