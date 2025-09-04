"""Основной модуль Telegram бота с современной архитектурой."""

import asyncio
import logging
from typing import Optional
from telegram import Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from django.conf import settings

from .config.settings import bot_settings
from .services import (
    VerificationService,
    UserService,
    PhoneService,
    RateLimitService,
    MessageService
)
from .handlers import (
    StartHandler,
    ContactHandler,
    CallbackHandler
)
from .exceptions import ConfigurationError, TelegramBotError

# Настройка логирования
logging.basicConfig(
    format=bot_settings.log_format,
    level=getattr(logging, bot_settings.log_level)
)
logger = logging.getLogger(__name__)

# Глобальные переменные для singleton
_bot_instance: Optional['TelegramBot'] = None
_bot_application: Optional[Application] = None


class TelegramBot:
    """Основной класс Telegram бота с современной архитектурой."""
    
    def __init__(self, token: str):
        """Инициализирует бота с зависимостями."""
        self.token = token
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        
        # Инициализируем сервисы
        self._init_services()
        
        # Инициализируем обработчики
        self._init_handlers()
        
        logger.info("TelegramBot инициализирован с современной архитектурой")
    
    def _init_services(self) -> None:
        """Инициализирует сервисы (Dependency Injection)."""
        try:
            # Создаем сервисы
            self.verification_service = VerificationService()
            self.user_service = UserService()
            self.phone_service = PhoneService()
            self.rate_limit_service = RateLimitService()
            
            # MessageService создается после инициализации бота
            self.message_service: Optional[MessageService] = None
            
            logger.info("Сервисы успешно инициализированы")
        except Exception as e:
            logger.error(f"Ошибка инициализации сервисов: {e}")
            raise ConfigurationError(f"Не удалось инициализировать сервисы: {e}")
    
    def _init_handlers(self) -> None:
        """Инициализирует обработчики команд."""
        try:
            # Обработчики будут созданы после инициализации message_service
            self.start_handler: Optional[StartHandler] = None
            self.contact_handler: Optional[ContactHandler] = None
            self.callback_handler: Optional[CallbackHandler] = None
            
            logger.info("Обработчики подготовлены к инициализации")
        except Exception as e:
            logger.error(f"Ошибка подготовки обработчиков: {e}")
            raise ConfigurationError(f"Не удалось подготовить обработчики: {e}")
    
    def _create_handlers(self) -> None:
        """Создает обработчики с внедренными зависимостями."""
        try:
            # Создаем обработчики с внедрением зависимостей
            self.start_handler = StartHandler(
                verification_service=self.verification_service,
                user_service=self.user_service,
                phone_service=self.phone_service,
                rate_limit_service=self.rate_limit_service,
                message_service=self.message_service
            )
            
            self.contact_handler = ContactHandler(
                verification_service=self.verification_service,
                user_service=self.user_service,
                phone_service=self.phone_service,
                rate_limit_service=self.rate_limit_service,
                message_service=self.message_service
            )
            
            self.callback_handler = CallbackHandler(
                verification_service=self.verification_service,
                user_service=self.user_service,
                phone_service=self.phone_service,
                rate_limit_service=self.rate_limit_service,
                message_service=self.message_service
            )
            
            logger.info("Обработчики успешно созданы с внедренными зависимостями")
        except Exception as e:
            logger.error(f"Ошибка создания обработчиков: {e}")
            raise ConfigurationError(f"Не удалось создать обработчики: {e}")
    
    def start_bot(self) -> None:
        """Запускает бота в синхронном режиме."""
        try:
            # Создаем приложение
            self.application = Application.builder().token(self.token).build()
            self.bot = self.application.bot
            
            # Создаем MessageService с ботом
            self.message_service = MessageService(self.bot)
            
            # Создаем обработчики
            self._create_handlers()
            
            # Настраиваем обработчики
            self._setup_handlers()
            
            logger.info("Telegram бот запущен")
            
            # Запуск бота в режиме polling
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise TelegramBotError(f"Не удалось запустить бота: {e}")
    
    async def start_bot_async(self) -> None:
        """Запускает бота в асинхронном режиме."""
        try:
            # Создаем приложение
            self.application = Application.builder().token(self.token).build()
            self.bot = self.application.bot
            
            # Создаем MessageService с ботом
            self.message_service = MessageService(self.bot)
            
            # Создаем обработчики
            self._create_handlers()
            
            # Настраиваем обработчики
            self._setup_handlers()
            
            # Инициализируем приложение
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Telegram бот запущен асинхронно")
            
            # Запуск polling
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
            
            # Ожидаем завершения
            await self.application.updater.idle()
            
        except Exception as e:
            logger.error(f"Ошибка при асинхронном запуске бота: {e}")
            raise TelegramBotError(f"Не удалось запустить бота асинхронно: {e}")
        finally:
            await self.stop_bot()
    
    async def stop_bot(self) -> None:
        """Останавливает бота корректно."""
        if self.application:
            try:
                logger.info("Начинаем остановку Telegram бота...")
                
                # Останавливаем updater
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                    logger.info("Updater остановлен")
                
                # Останавливаем приложение
                if self.application.running:
                    await self.application.stop()
                    logger.info("Application остановлено")
                
                # Завершаем приложение
                await self.application.shutdown()
                logger.info("Application завершено")
                
                logger.info("Telegram бот успешно остановлен")
                
            except Exception as e:
                logger.error(f"Ошибка при остановке бота: {e}")
            finally:
                self.application = None
                self.bot = None
    
    def _setup_handlers(self) -> None:
        """Настраивает обработчики команд и сообщений."""
        try:
            if not self.application:
                raise ConfigurationError("Application не инициализировано")
            
            # Команды
            self.application.add_handler(
                CommandHandler("start", self.start_handler)
            )
            
            # Callback запросы
            self.application.add_handler(
                CallbackQueryHandler(self.callback_handler)
            )
            
            # Контакты
            self.application.add_handler(
                MessageHandler(filters.CONTACT, self.contact_handler)
            )
            
            # Обработчик ошибок
            self.application.add_error_handler(self._error_handler)
            
            logger.info("Обработчики команд настроены")
            
        except Exception as e:
            logger.error(f"Ошибка настройки обработчиков: {e}")
            raise ConfigurationError(f"Не удалось настроить обработчики: {e}")
    
    async def _error_handler(self, update, context) -> None:
        """Глобальный обработчик ошибок."""
        try:
            error = context.error
            logger.error(
                f"Глобальная ошибка в боте: {error}",
                extra={
                    'update': update.to_dict() if update else None,
                    'error_type': type(error).__name__
                },
                exc_info=True
            )
            
            # Пытаемся отправить пользователю сообщение об ошибке
            if update and update.effective_chat:
                try:
                    await self.message_service.send_error_message(
                        chat_id=str(update.effective_chat.id),
                        error_type='general'
                    )
                except Exception as send_error:
                    logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")
                    
        except Exception as handler_error:
            logger.critical(f"Критическая ошибка в обработчике ошибок: {handler_error}")
    
    def get_bot_info(self) -> dict:
        """Возвращает информацию о боте."""
        return {
            'is_running': self.application is not None and self.application.running,
            'bot_username': self.bot.username if self.bot else None,
            'handlers_count': len(self.application.handlers[0]) if self.application else 0,
            'services_initialized': all([
                self.verification_service is not None,
                self.user_service is not None,
                self.phone_service is not None,
                self.rate_limit_service is not None,
                self.message_service is not None
            ])
        }


def get_bot_instance() -> TelegramBot:
    """Получение экземпляра бота (singleton pattern)."""
    global _bot_instance
    
    if _bot_instance is None:
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN не настроен в settings")
        
        _bot_instance = TelegramBot(bot_token)
        logger.info("Создан новый экземпляр Telegram бота")
    
    return _bot_instance


# Функции для обратной совместимости с существующим кодом
async def send_verification_code_to_telegram(
    chat_id: str, 
    verification_type: str = 'registration'
) -> Optional[str]:
    """Функция для отправки кода верификации через бота."""
    try:
        bot = get_bot_instance()
        if not bot.message_service:
            logger.error("MessageService не инициализирован")
            return None
        
        # Здесь должна быть логика получения кода верификации
        # Пока возвращаем None для совместимости
        logger.warning("send_verification_code_to_telegram: функция требует рефакторинга")
        return None
        
    except Exception as e:
        logger.error(f"Ошибка отправки кода верификации: {e}")
        return None


async def send_login_request_to_telegram(
    chat_id: str, 
    phone_number: str, 
    verification_code: str
) -> bool:
    """Функция для отправки запроса на вход через Telegram."""
    try:
        bot = get_bot_instance()
        if not bot.message_service:
            logger.error("MessageService не инициализирован")
            return False
        
        return await bot.message_service.send_login_request(
            chat_id=chat_id,
            phone=phone_number
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки запроса на вход: {e}")
        return False


async def send_phone_change_code_to_telegram(
    chat_id: str, 
    verification_code: str, 
    current_phone: str, 
    verification_type: str
) -> bool:
    """Функция для отправки кода смены номера телефона."""
    try:
        bot = get_bot_instance()
        if not bot.message_service:
            logger.error("MessageService не инициализирован")
            return False
        
        # Определяем текст сообщения в зависимости от типа
        if verification_type == 'phone_change_current':
            message_text = (
                f"📱 Подтверждение текущего номера телефона\n\n"
                f"Ваш текущий номер: {current_phone}\n\n"
                f"🔐 Код подтверждения: {verification_code}\n\n"
                f"Введите этот код на сайте для подтверждения текущего номера.\n\n"
                f"⏰ Код действителен в течение 10 минут."
            )
        else:
            message_text = (
                f"📱 Код для смены номера телефона\n\n"
                f"🔐 Код подтверждения: {verification_code}\n\n"
                f"Введите этот код на сайте для завершения смены номера.\n\n"
                f"⏰ Код действителен в течение 10 минут."
            )
        
        return await bot.message_service.send_simple_message(
            chat_id=chat_id,
            text=message_text
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки кода смены номера: {e}")
        return False


async def send_password_reset_link_to_telegram(
    chat_id: str, 
    reset_url: str, 
    user_name: str
) -> bool:
    """Функция для отправки ссылки сброса пароля."""
    try:
        bot = get_bot_instance()
        if not bot.message_service:
            logger.error("MessageService не инициализирован")
            return False
        
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Создаем клавиатуру с кнопкой для перехода по ссылке
        keyboard = [[
            InlineKeyboardButton("🔐 Сбросить пароль", url=reset_url)
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Текст сообщения
        reset_text = (
            f"🔐 Сброс пароля\n\n"
            f"Привет, {user_name}!\n\n"
            f"Вы запросили сброс пароля для вашего аккаунта. "
            f"Нажмите кнопку ниже, чтобы установить новый пароль.\n\n"
            f"⚠️ Ссылка действительна в течение 1 часа.\n\n"
            f"Если вы не запрашивали сброс пароля, просто проигнорируйте это сообщение."
        )
        
        return await bot.message_service.send_simple_message(
            chat_id=chat_id,
            text=reset_text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки ссылки сброса пароля: {e}")
        return False
