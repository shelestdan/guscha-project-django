"""Обработчик команды /start."""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import CommandHandler
from ..exceptions import VerificationCodeError

logger = logging.getLogger(__name__)


class StartHandler(CommandHandler):
    """Обработчик команды /start."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start."""
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        
        self.log_handler_start('start_command', user_info)
        
        # Проверяем rate limit
        await self.check_rate_limit(chat_id, 'start_command')
        
        try:
            # Получаем параметры команды
            args = self.extract_command_args(context)
            verification_id = None
            is_login = False
            is_phone_change = False
            is_register = False
            
            if args:
                param = args[0]
                self.logger.info(f"Получен параметр команды /start: {param}")
                
                if param.startswith('login_'):
                    verification_id = param[6:]  # Убираем префикс 'login_'
                    is_login = True
                    self.logger.info(f"Обнаружен login параметр: {verification_id}")
                elif param.startswith('phone_change_'):
                    # Обработка смены номера телефона
                    verification_code = param[13:]  # Убираем префикс 'phone_change_'
                    await self._handle_phone_change_start(update, verification_code)
                    return
                elif param.startswith('register_'):
                    verification_id = param[9:]  # Убираем префикс 'register_'
                    is_register = True
                    self.logger.info(f"Обнаружен register параметр: {verification_id}")
                else:
                    verification_id = param
                    self.logger.info(f"Обнаружен обычный параметр: {verification_id}")
            
            # Ищем код верификации
            verification_code = await self.verification_service.find_verification_code(
                chat_id=chat_id,
                verification_id=verification_id,
                is_login=is_login
            )
            
            # Обновляем код верификации если найден
            if verification_code:
                await self.verification_service.update_verification_code(
                    verification_code=verification_code,
                    chat_id=chat_id
                )
                
                # Обновляем информацию о пользователе
                if verification_code.user:
                    await self.user_service.update_telegram_info(
                        user=verification_code.user,
                        chat_id=chat_id,
                        username=user_info['username']
                    )
                
                # Обрабатываем QR-код если это QR-регистрация
                if verification_code.verification_type == 'qr_registration':
                    await self._handle_qr_code_start(verification_code, chat_id)
            
            # Отправляем приветственное сообщение
            await self._send_welcome_message(
                user_info=user_info,
                verification_code=verification_code,
                is_login=is_login,
                is_register=is_register
            )
            
            self.log_handler_success(
                'start_command',
                user_info,
                {
                    'has_verification_code': verification_code is not None,
                    'verification_type': verification_code.verification_type if verification_code else None,
                    'is_login': is_login,
                    'is_register': is_register
                }
            )
            
        except Exception as e:
            await self.handle_error(update, context, e, 'start_command')
    
    async def _handle_phone_change_start(
        self,
        update: Update,
        verification_code: str
    ) -> None:
        """Обрабатывает начало смены номера телефона."""
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        
        self.logger.info(f"Обработка смены номера для chat_id={chat_id}, code={verification_code}")
        
        try:
            # Находим код верификации для смены номера
            phone_change_code = await self.verification_service.find_verification_code(
                chat_id=None,  # Не ищем по chat_id, так как он еще не привязан
                verification_id=verification_code
            )
            
            if not phone_change_code or phone_change_code.verification_type != 'phone_change_new':
                await self.message_service.send_error_message(
                    chat_id=chat_id,
                    error_type='no_verification_code'
                )
                return
            
            # Проверяем соответствие кода
            display_code = await self.verification_service.generate_display_code(phone_change_code)
            if display_code != verification_code:
                await self.message_service.send_error_message(
                    chat_id=chat_id,
                    error_type='no_verification_code'
                )
                return
            
            # Отправляем запрос на смену номера
            new_phone = phone_change_code.telegram_phone or "не указан"
            await self.message_service.send_phone_change_request(
                chat_id=chat_id,
                new_phone=new_phone,
                verification_code=verification_code
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке смены номера: {e}")
            await self.message_service.send_error_message(
                chat_id=chat_id,
                error_type='general'
            )
    
    async def _handle_qr_code_start(
        self,
        verification_code,
        chat_id: str
    ) -> None:
        """Обрабатывает запуск через QR-код."""
        try:
            # Пытаемся связать QR-код с существующим пользователем
            if not verification_code.user:
                self.logger.info(f"QR-код {verification_code.id} не связан с пользователем, ищем пользователя с chat_id={chat_id}")
                
                existing_user = await self.user_service.get_user_by_chat_id(chat_id)
                if existing_user:
                    await self.verification_service.update_verification_code(
                        verification_code=verification_code,
                        user=existing_user
                    )
                    self.logger.info(f"QR-код {verification_code.id} успешно связан с пользователем {existing_user.id}")
            
            # Отмечаем запуск бота для QR-кода
            display_code = await self.verification_service.generate_display_code(verification_code)
            await self.verification_service.handle_qr_code_verification(verification_code, display_code)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки QR-кода: {e}")
            # Не прерываем процесс, продолжаем с обычным приветствием
    
    async def _send_welcome_message(
        self,
        user_info: dict,
        verification_code,
        is_login: bool = False,
        is_register: bool = False
    ) -> None:
        """Отправляет приветственное сообщение."""
        chat_id = user_info['chat_id']
        first_name = user_info['first_name'] or 'Пользователь'
        
        # Определяем тип верификации и QR-код
        verification_type = None
        is_qr_code = False
        has_verification_code = verification_code is not None
        
        if verification_code:
            verification_type = verification_code.verification_type
            is_qr_code = verification_type == 'qr_registration'
        
        # Отправляем приветственное сообщение
        await self.message_service.send_welcome_message(
            chat_id=chat_id,
            first_name=first_name,
            verification_type=verification_type,
            is_qr_code=is_qr_code,
            has_verification_code=has_verification_code
        )
        
        self.logger.info(
            f"Приветственное сообщение отправлено: "
            f"verification_type={verification_type}, is_qr_code={is_qr_code}, "
            f"has_code={has_verification_code}"
        )