"""Сервис для отправки сообщений в Telegram."""

import logging
from typing import Optional, List, Dict, Any
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CopyTextButton
from telegram.error import TelegramError

from ..config.settings import bot_settings
from ..config.messages import messages
from ..exceptions import MessageSendError
from ..utils.formatters import MessageFormatter

logger = logging.getLogger(__name__)


class MessageService:
    """Сервис для отправки сообщений в Telegram."""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot or Bot(token=bot_settings.token)
        self.formatter = MessageFormatter()
    
    async def send_welcome_message(
        self,
        chat_id: str,
        first_name: str,
        verification_type: Optional[str] = None,
        is_qr_code: bool = False,
        has_verification_code: bool = True
    ) -> bool:
        """Отправляет приветственное сообщение."""
        try:
            # Формируем текст сообщения
            welcome_text = self.formatter.format_welcome_message(
                first_name=first_name,
                verification_type=verification_type,
                is_qr_code=is_qr_code
            )
            
            # Создаем клавиатуру если есть код верификации
            reply_markup = None
            if has_verification_code:
                keyboard = [[
                    InlineKeyboardButton(
                        messages.BUTTON_AGREE_SMS, 
                        callback_data="agree_sms"
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=welcome_text,
                reply_markup=reply_markup
            )
            
            logger.info(f"Приветственное сообщение отправлено в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки приветственного сообщения в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки приветственного сообщения: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def send_verification_code(
        self,
        chat_id: str,
        code: str,
        verification_type: str,
        timeout_minutes: int = 10
    ) -> bool:
        """Отправляет код верификации пользователю."""
        try:
            # Формируем текст с кодом
            code_text = self.formatter.format_verification_code_message(
                code=code,
                verification_type=verification_type,
                timeout_minutes=timeout_minutes
            )
            
            # Логируем отправляемый текст для отладки
            logger.info(f"Отправляемый текст: {repr(code_text)}")
            
            # Создаем кнопку для копирования кода
            copy_button = CopyTextButton(text=code)
            keyboard = [[
                InlineKeyboardButton(
                    messages.BUTTON_COPY_CODE,
                    copy_text=copy_button
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=code_text,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            
            logger.info(f"Код верификации отправлен в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки кода верификации в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки кода верификации: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def send_phone_request(
        self,
        chat_id: str,
        message_text: Optional[str] = None
    ) -> bool:
        """Отправляет запрос на предоставление номера телефона."""
        try:
            # Используем переданный текст или стандартный
            text = message_text or messages.PHONE_SHARE_REQUEST
            
            # Создаем клавиатуру с кнопкой для запроса контакта
            contact_keyboard = KeyboardButton(
                messages.BUTTON_SHARE_PHONE, 
                request_contact=True
            )
            reply_markup = ReplyKeyboardMarkup(
                [[contact_keyboard]], 
                one_time_keyboard=True, 
                resize_keyboard=True
            )
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=text,
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос номера телефона отправлен в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса номера телефона в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки запроса номера телефона: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def send_error_message(
        self,
        chat_id: str,
        error_type: str,
        **kwargs
    ) -> bool:
        """Отправляет сообщение об ошибке."""
        try:
            # Определяем текст ошибки
            error_messages = {
                'no_verification_code': messages.ERROR_NO_VERIFICATION_CODE,
                'code_expired': messages.ERROR_CODE_EXPIRED,
                'phone_mismatch': messages.ERROR_PHONE_MISMATCH,
                'no_phone': messages.ERROR_NO_PHONE,
                'general': messages.ERROR_GENERAL,
                'rate_limit': messages.ERROR_RATE_LIMIT,
            }
            
            error_text = error_messages.get(error_type, messages.ERROR_GENERAL)
            
            # Форматируем сообщение с параметрами
            if kwargs:
                error_text = messages.format_message(error_text, **kwargs)
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=error_text
            )
            
            logger.info(f"Сообщение об ошибке '{error_type}' отправлено в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения об ошибке в chat_id {chat_id}: {e}")
            return False
    
    async def send_registration_confirmation(
        self,
        chat_id: str,
        phone: str
    ) -> bool:
        """Отправляет запрос на подтверждение регистрации."""
        try:
            # Формируем текст сообщения
            confirmation_text = self.formatter.format_registration_confirm_message(phone)
            
            # Создаем кнопки подтверждения
            keyboard = [
                [InlineKeyboardButton(
                    messages.BUTTON_CONFIRM_REGISTRATION,
                    callback_data=f"confirm_registration_{chat_id}"
                )],
                [InlineKeyboardButton(
                    messages.BUTTON_CANCEL,
                    callback_data="cancel_registration"
                )]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=confirmation_text,
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос подтверждения регистрации отправлен в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса подтверждения регистрации в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки запроса подтверждения регистрации: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def send_login_request(
        self,
        chat_id: str,
        phone: str
    ) -> bool:
        """Отправляет запрос на вход через Telegram."""
        try:
            # Формируем текст сообщения
            login_text = self.formatter.format_login_request_message(phone)
            
            # Создаем клавиатуру с кнопкой для запроса контакта
            contact_keyboard = KeyboardButton(
                messages.BUTTON_SHARE_PHONE,
                request_contact=True
            )
            reply_markup = ReplyKeyboardMarkup(
                [[contact_keyboard]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=login_text,
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос на вход отправлен в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса на вход в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки запроса на вход: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def send_phone_change_request(
        self,
        chat_id: str,
        new_phone: str,
        verification_code: str
    ) -> bool:
        """Отправляет запрос на смену номера телефона."""
        try:
            # Формируем текст сообщения
            change_text = self.formatter.format_phone_change_request_message(new_phone)
            
            # Создаем кнопку согласия
            keyboard = [[
                InlineKeyboardButton(
                    messages.BUTTON_AGREE_DATA_PROCESSING,
                    callback_data=f"agree_phone_change_{verification_code}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=change_text,
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос смены номера отправлен в chat_id {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки запроса смены номера в chat_id {chat_id}: {e}")
            raise MessageSendError(
                f"Ошибка отправки запроса смены номера: {e}",
                chat_id=chat_id,
                telegram_error=e
            )
    
    async def remove_keyboard(self, chat_id: str, text: str = "Клавиатура удалена") -> bool:
        """Удаляет клавиатуру."""
        try:
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=text,
                reply_markup=ReplyKeyboardRemove()
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления клавиатуры в chat_id {chat_id}: {e}")
            return False
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """Редактирует сообщение."""
        try:
            await self.bot.edit_message_text(
                chat_id=int(chat_id),
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения в chat_id {chat_id}: {e}")
            return False
    
    async def send_simple_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Отправляет простое текстовое сообщение."""
        try:
            await self.bot.send_message(
                chat_id=int(chat_id),
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в chat_id {chat_id}: {e}")
            return False