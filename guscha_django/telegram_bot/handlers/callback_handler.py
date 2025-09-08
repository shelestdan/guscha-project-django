"""Обработчик callback запросов."""

import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandler
from ..exceptions import VerificationCodeError, ValidationError

logger = logging.getLogger(__name__)


class CallbackHandler(BaseHandler):
    """Обработчик callback запросов от inline кнопок."""
    
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
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает callback запросы."""
        query = update.callback_query
        if not query:
            return
        
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        callback_data = query.data
        
        self.log_handler_start('callback_handler', user_info, {'callback_data': callback_data})
        
        # Отвечаем на callback query
        await self.answer_callback_query(update)
        
        # Проверяем rate limit
        await self.check_rate_limit(chat_id, 'callback_query')
        
        try:
            # Парсим callback data
            action, param = self.parse_callback_data(callback_data)
            
            # Маршрутизируем по действиям
            if action == 'agree' and param == 'sms':
                await self._handle_agree_sms(update, context)
            elif action == 'agree' and param and param.startswith('phone_change_'):
                verification_code = param[13:]  # Убираем 'phone_change_'
                await self._handle_agree_phone_change(update, context, verification_code)
            elif action == 'confirm' and param and param.startswith('registration_'):
                verification_id = param[13:]  # Убираем 'registration_'
                await self._handle_confirm_registration(update, context, verification_id)
            elif action == 'cancel' and param == 'registration':
                await self._handle_cancel_registration(update, context)
            else:
                self.logger.warning(f"Неизвестный callback: {callback_data}")
                await self.message_service.send_simple_message(
                    chat_id=chat_id,
                    text="❌ Неизвестная команда"
                )
            
            self.log_handler_success(
                'callback_handler',
                user_info,
                {'action': action, 'param': param}
            )
            
        except Exception as e:
            await self.handle_error(update, context, e, f'callback_handler:{callback_data}')
    
    async def _handle_agree_sms(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает согласие на SMS."""
        query = update.callback_query
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        
        try:
            # Ищем активный код верификации
            verification_code = await self._find_comprehensive_verification_code(chat_id)
            
            if not verification_code:
                await query.edit_message_text(
                    text="❌ Активный код верификации не найден.\n\n"
                         "Пожалуйста, сначала зарегистрируйтесь на сайте."
                )
                return
            
            # Проверяем, не истек ли код
            if await self.verification_service.is_expired(verification_code):
                await query.edit_message_text(
                    text="⏰ Код верификации истек.\n\n"
                         "Пожалуйста, повторите процесс регистрации на сайте."
                )
                return
            
            self.logger.info(f"Найден активный код {verification_code.id}, тип: {verification_code.verification_type}")
            
            # Подтверждаем готовность к получению контакта
            await query.edit_message_text(
                text="✅ Код верификации готов к использованию."
            )
            
            # Отправляем сообщение с кнопкой запроса контакта
            await self.message_service.send_phone_request(chat_id)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке согласия на SMS: {e}")
            await query.edit_message_text(
                text="❌ Произошла ошибка при генерации кода.\n\n"
                     "Пожалуйста, попробуйте позже."
            )
    
    async def _handle_agree_phone_change(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        verification_code: str
    ) -> None:
        """Обрабатывает согласие на смену номера телефона."""
        query = update.callback_query
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        
        self.logger.info(f"Согласие на смену номера от chat_id={chat_id}, code={verification_code}")
        
        try:
            # Находим код верификации для смены номера
            phone_change_code = await self.verification_service.find_verification_code(
                chat_id=None,
                verification_id=verification_code
            )
            
            if not phone_change_code or phone_change_code.verification_type != 'phone_change_new':
                await query.edit_message_text(
                    text="❌ Не найден активный запрос на смену номера.\n\n"
                         "Повторите процедуру смены номера на сайте."
                )
                return
            
            # Проверяем соответствие кода
            display_code = await self.verification_service.generate_display_code(phone_change_code)
            if display_code != verification_code:
                await query.edit_message_text(
                    text="❌ Неверный код верификации.\n\n"
                         "Повторите процедуру смены номера."
                )
                return
            
            # Обновляем chat_id в коде верификации
            await self.verification_service.update_verification_code(
                verification_code=phone_change_code,
                chat_id=chat_id
            )
            
            # Запрашиваем контакт пользователя
            await query.edit_message_text(
                text="📱 Теперь поделитесь вашим номером телефона.\n\n"
                     "Мы сверим его с новым номером, указанным на сайте."
            )
            
            await self.message_service.send_phone_request(chat_id)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке согласия на смену номера: {e}")
            await query.edit_message_text(
                text="❌ Произошла ошибка.\n\n"
                     "Повторите процедуру позже."
            )
    
    async def _handle_confirm_registration(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        verification_id: str
    ) -> None:
        """Обрабатывает подтверждение создания нового аккаунта."""
        query = update.callback_query
        user_info = self.get_user_info(update)
        chat_id = user_info['chat_id']
        
        try:
            # Проверяем ограничение частоты регистрации
            if not await self.rate_limit_service.check_registration_rate_limit(chat_id):
                await query.edit_message_text(
                    text="❌ Слишком много попыток регистрации.\n\n"
                         "Попробуйте позже (через 5 минут)."
                )
                return
            
            # Получаем код верификации через комплексный поиск
            # verification_id на самом деле содержит chat_id
            self.logger.info(f"Поиск кода верификации для chat_id: {verification_id}")
            verification_code = await self._find_comprehensive_verification_code(verification_id)
            
            self.logger.info(f"Проверка кода верификации для chat_id {verification_id}:")
            self.logger.info(f"Код найден: {verification_code is not None}")
            if verification_code:
                self.logger.info(f"ID найденного кода: {verification_code.id}")
                self.logger.info(f"Chat ID кода: {verification_code.telegram_chat_id}, текущий chat_id: {chat_id}")
                self.logger.info(f"Код использован: {verification_code.is_used}")
                self.logger.info(f"Тип кода: {verification_code.verification_type}")
            
            if not verification_code:
                self.logger.warning(f"Код верификации для chat_id {verification_id} не найден")
                await query.edit_message_text(
                    text="❌ Код верификации не найден или уже использован.\n\n"
                         "Пожалуйста, повторите процесс регистрации."
                )
                return
                
            if verification_code.is_used:
                self.logger.warning(f"Код верификации {verification_id} уже использован")
                await query.edit_message_text(
                    text="❌ Код верификации не найден или уже использован.\n\n"
                         "Пожалуйста, повторите процесс регистрации."
                )
                return
                
            # Проверяем chat_id только если он установлен
            if verification_code.telegram_chat_id and str(verification_code.telegram_chat_id) != chat_id:
                self.logger.warning(f"Chat ID не совпадает: код={verification_code.telegram_chat_id}, текущий={chat_id}")
                await query.edit_message_text(
                    text="❌ Код верификации не найден или уже использован.\n\n"
                         "Пожалуйста, повторите процесс регистрации."
                )
                return
            
            # Проверяем, что код не истек
            if await self.verification_service.is_expired(verification_code):
                await query.edit_message_text(
                    text="❌ Код верификации истек.\n\n"
                         "Пожалуйста, повторите процесс регистрации."
                )
                return
            
            # Получаем номер телефона из кода верификации
            phone_number = verification_code.telegram_phone
            if not phone_number:
                await query.edit_message_text(
                    text="❌ Ошибка: номер телефона не найден.\n\n"
                         "Пожалуйста, повторите процесс регистрации."
                )
                return
            
            # Создаем нового пользователя
            user = await self.user_service.create_telegram_user(
                phone=phone_number,
                chat_id=chat_id,
                telegram_username=user_info['username'],
                first_name=user_info['first_name'],
                last_name=user_info['last_name']
            )
            
            # Привязываем пользователя к коду верификации
            await self.verification_service.verification_repo.link_user(verification_code, user)
            await self.verification_service.mark_as_used(verification_code)
            
            # Обновляем chat_id для кода верификации
            await self.verification_service.verification_repo.update_chat_id(verification_code, chat_id)
            
            # Отправляем сообщение об успешной регистрации
            success_text = (
                f"✅ Аккаунт успешно создан!\n\n"
                f"📱 Номер телефона: {self.phone_service.format_for_display(phone_number)}\n\n"
                f"💡 Рекомендуем заполнить профиль в личном кабинете на сайте.\n\n"
                f"🔐 Для входа используйте свой номер телефона."
            )
            
            await query.edit_message_text(text=success_text)
            
            self.logger.info(f"Успешно создан новый пользователь {user.id} через Telegram для номера {self.phone_service.get_phone_hash(phone_number)}")
            
        except ValidationError as ve:
            self.logger.warning(f"Validation error in registration: {ve}")
            await query.edit_message_text(
                text=f"❌ {str(ve)}\n\n"
                     f"Попробуйте еще раз или обратитесь в поддержку."
            )
        except Exception as e:
            self.logger.error(f"Ошибка при создании аккаунта: {e}")
            await query.edit_message_text(
                text="❌ Произошла ошибка при создании аккаунта.\n\n"
                     "Пожалуйста, попробуйте позже."
            )
    
    async def _handle_cancel_registration(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Обрабатывает отмену регистрации."""
        query = update.callback_query
        user_info = self.get_user_info(update)
        
        await query.edit_message_text(
            text="❌ Регистрация отменена.\n\n"
                 "Если вы передумаете, можете повторить процесс позже."
        )
        
        self.logger.info(f"Пользователь {user_info['user_id']} отменил регистрацию")