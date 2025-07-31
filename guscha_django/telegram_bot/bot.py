import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
from apps.accounts.models import User, TelegramVerificationCode, QRCodeScan
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра бота
_bot_instance = None
_bot_application = None


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None
        
    def start_bot(self):
        """Запуск бота"""
        try:
            self.application = Application.builder().token(self.token).build()
            self.setup_handlers()
            
            logger.info("Telegram бот запущен")
            
            # Запуск бота в режиме polling (синхронный метод)
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise
        
    async def stop_bot(self):
        """Остановка бота"""
        if self.application:
            try:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                if self.application.running:
                    await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram бот остановлен")
            except Exception as e:
                logger.error(f"Ошибка при остановке бота: {e}")
            finally:
                self.application = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Получаем verification_id из параметров команды
        verification_id = None
        is_login = False
        
        if context.args:
            param = context.args[0]
            # Проверяем, это логин или обычная верификация
            if param.startswith('login_'):
                verification_id = param[6:]  # Убираем префикс 'login_'
                is_login = True
            else:
                verification_id = param
        
        # Проверяем, есть ли активный код верификации
        verification_code = None
        is_qr_code = False
        
        if verification_id:
            try:
                verification_code = await sync_to_async(TelegramVerificationCode.objects.get)(
                    code=verification_id,
                    is_used=False
                )
                if not await sync_to_async(verification_code.is_expired)():
                    # Обновляем chat_id в коде верификации
                    verification_code.telegram_chat_id = str(chat_id)
                    await sync_to_async(verification_code.save)()
                    
                    # Проверяем, является ли это QR-кодом
                    if verification_code.verification_type == 'qr_registration':
                        is_qr_code = True
                        # Отмечаем запуск бота для QR-кода
                        await self.mark_qr_bot_started(verification_code.code)
                    
                    # Обновляем пользователя (только если это не регистрация)
                    try:
                        user_obj = await sync_to_async(lambda: verification_code.user)()
                        if user_obj:
                            user_obj.telegram_chat_id = str(chat_id)
                            if user.username:
                                user_obj.telegram_username = user.username
                            await sync_to_async(user_obj.save)()
                    except Exception as e:
                        # Если пользователь не связан - это нормально для некоторых типов верификации
                        logger.debug(f"Пользователь не связан с кодом верификации {verification_id}: {e}")
                    
                    logger.info(f"Связан пользователь {chat_id} с кодом верификации {verification_id}")
                else:
                    verification_code = None
            except TelegramVerificationCode.DoesNotExist:
                verification_code = None
        
        if not verification_code:
            # Ищем любой активный код для этого chat_id
            verification_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=str(chat_id),
                    is_used=False
                ).order_by('-created_at').first
            )()
        
        # Создаем клавиатуру с кнопкой согласия
        keyboard = [[
            InlineKeyboardButton("✅ Соглашаюсь на отправку SMS", callback_data="agree_sms")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if verification_code:
            verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
            
            if is_qr_code:
                welcome_text = (
                    f"Привет, {user.first_name}! 👋\n\n"
                    f"✅ QR-код успешно отсканирован!\n\n"
                    "Нажмите кнопку ниже, чтобы получить код подтверждения:"
                )
            else:
                welcome_text = (
                    f"Привет, {user.first_name}! 👋\n\n"
                    f"Найден активный код верификации для {verification_type_display.lower()}.\n\n"
                    "Нажмите кнопку ниже, чтобы получить код подтверждения:"
                )
        else:
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                "Этот бот поможет вам подтвердить ваш аккаунт.\n\n"
                "Сначала зарегистрируйтесь на сайте, а затем вернитесь сюда для получения кода."
            )
            reply_markup = None
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup
        )
        
    def normalize_phone_number(self, phone_number: str) -> str:
        """Нормализует номер телефона для сравнения"""
        if not phone_number:
            return ""
        
        # Удаляем все символы кроме цифр и знака +
        normalized = re.sub(r'[^\d+]', '', phone_number)
        
        # Если номер начинается с 8, заменяем на +7 (для российских номеров)
        if normalized.startswith('8') and len(normalized) == 11:
            normalized = '+7' + normalized[1:]
        
        # Если номер начинается с 7 без +, добавляем +
        elif normalized.startswith('7') and len(normalized) == 11:
            normalized = '+' + normalized
            
        return normalized
    
    async def agree_sms_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик согласия на SMS"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.from_user.id
        username = query.from_user.username
        
        try:
            # Ищем активный код верификации для этого chat_id
            # Сначала пробуем найти по chat_id (для обычной регистрации)
            verification_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=str(chat_id),
                    is_used=False
                ).order_by('-created_at').first
            )()
            
            # Если не найден, ищем код входа для пользователя с этим chat_id
            if not verification_code:
                # Ищем пользователя с этим chat_id
                user_with_chat_id = await sync_to_async(
                    User.objects.filter(telegram_chat_id=str(chat_id)).first
                )()
                
                if user_with_chat_id:
                    # Ищем активный код входа для этого пользователя
                    verification_code = await sync_to_async(
                        TelegramVerificationCode.objects.filter(
                            user=user_with_chat_id,
                            verification_type='login',
                            is_used=False
                        ).order_by('-created_at').first
                    )()
            
            if not verification_code:
                await query.edit_message_text(
                    "❌ Активный код верификации не найден.\n\n"
                    "Пожалуйста, сначала зарегистрируйтесь на сайте."
                )
                return
                
            if await sync_to_async(verification_code.is_expired)():
                await query.edit_message_text(
                    "⏰ Код верификации истек.\n\n"
                    "Пожалуйста, повторите процесс регистрации на сайте."
                )
                return
            
            # Запрашиваем контакт пользователя для проверки номера телефона
            contact_keyboard = KeyboardButton("📱 Поделиться номером телефона", request_contact=True)
            reply_markup = ReplyKeyboardMarkup([[contact_keyboard]], one_time_keyboard=True, resize_keyboard=True)
            
            await query.edit_message_text(
                "📱 Для получения кода подтверждения необходимо поделиться номером телефона.\n\n"
                "Нажмите кнопку ниже, чтобы поделиться вашим номером телефона из Telegram:",
                reply_markup=None
            )
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text="👇 Нажмите кнопку для подтверждения номера телефона:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке согласия на SMS: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при генерации кода.\n\n"
                "Пожалуйста, попробуйте позже."
            )
    
    async def send_verification_code(self, chat_id: str, verification_type: str = 'registration') -> str:
        """Отправляет код верификации пользователю"""
        try:
            # Ищем активный код верификации
            verification_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=chat_id,
                    verification_type=verification_type,
                    is_used=False
                ).order_by('-created_at').first
            )()
            
            if not verification_code or await sync_to_async(verification_code.is_expired)():
                return None
                
            # Отправляем сообщение с кодом
            verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
            code_text = (
                f"🔐 Ваш код подтверждения: ||{verification_code.code}||\n\n"
                f"Введите этот код на сайте для завершения {verification_type_display.lower()}\.\n\n"
                f"⏰ Код действителен в течение 10 минут\."
            )
            
            await self.application.bot.send_message(
                chat_id=int(chat_id),
                text=code_text,
                parse_mode='MarkdownV2'
            )
            
            return verification_code.code
            
        except Exception as e:
            logger.error(f"Ошибка при отправке кода верификации: {e}")
            return None
    
    async def send_login_request(self, chat_id: str, phone_number: str, verification_code: str) -> bool:
        """Отправляет запрос на вход через Telegram"""
        try:
            if not chat_id:
                logger.warning(f"Пустой chat_id для запроса входа с номером {phone_number}")
                return False
            
            if not self.application or not self.application.bot:
                logger.error("Telegram бот не инициализирован")
                return False
            
            logger.info(f"Отправка запроса на вход: chat_id={chat_id}, phone={phone_number}, code={verification_code}")
            
            # Создаем клавиатуру с кнопкой для запроса номера телефона
            keyboard = [
                [KeyboardButton("📱 Поделиться номером телефона", request_contact=True)]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            # Отправляем сообщение с запросом на вход
            login_text = (
                f"🔐 Запрос на вход через Telegram\n\n"
                f"📱 Номер телефона с сайта: {phone_number}\n\n"
                f"Для подтверждения входа поделитесь своим номером телефона, "
                f"нажав кнопку ниже\. Мы сверим его с номером, указанным на сайте\."
            )
            
            await self.application.bot.send_message(
                chat_id=int(chat_id),
                text=login_text,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос на вход успешно отправлен в chat_id {chat_id} для номера {phone_number}")
            return True
            
        except ValueError as e:
            logger.error(f"Неверный chat_id '{chat_id}': {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отправке запроса на вход в chat_id {chat_id}: {e}")
            return False
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик получения контакта пользователя"""
        contact = update.message.contact
        chat_id = update.effective_chat.id
        
        try:
            # Удаляем клавиатуру
            await update.message.reply_text(
                "📱 Номер телефона получен, проверяем...",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Ищем активный код верификации для этого chat_id
            verification_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=str(chat_id),
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).order_by('-created_at').first
            )()
            
            # Также ищем коды для входа по chat_id из пользователя
            if not verification_code:
                # Ищем пользователя с этим chat_id
                user = await sync_to_async(
                    User.objects.filter(telegram_chat_id=str(chat_id)).first
                )()
                
                if user:
                    # Ищем активный код входа для этого пользователя
                    verification_code = await sync_to_async(
                        TelegramVerificationCode.objects.filter(
                            user=user,
                            verification_type='login',
                            is_used=False,
                            expires_at__gt=timezone.now()
                        ).order_by('-created_at').first
                    )()
            
            if not verification_code:
                logger.warning(f"Активный код верификации не найден для chat_id {chat_id}")
                await update.message.reply_text(
                    "❌ Активный код верификации не найден.\n"
                    "Пожалуйста, сначала зарегистрируйтесь на сайте или инициируйте вход."
                )
                return
                
            if await sync_to_async(verification_code.is_expired)():
                logger.warning(f"Код верификации {verification_code.id} истек")
                await update.message.reply_text(
                    "⏰ Код верификации истек.\n\n"
                    "Пожалуйста, повторите процесс регистрации на сайте."
                )
                return
            
            # Получаем номер телефона из контакта
            telegram_phone = self.normalize_phone_number(contact.phone_number)
            
            # Получаем связанного пользователя и pending_registration
            user = await sync_to_async(lambda: verification_code.user)()
            pending_registration = await sync_to_async(lambda: verification_code.pending_registration)()
            verification_type = await sync_to_async(lambda: verification_code.verification_type)()

            # Специальная обработка для входа через Telegram
            if verification_type == 'login':
                # Для входа проверяем номер телефона пользователя
                if not user:
                    logger.warning(f"Пользователь не найден для кода входа {verification_code.id}")
                    await update.message.reply_text(
                        "❌ Ошибка: пользователь не найден.\n\n"
                        "Пожалуйста, повторите процесс входа на сайте."
                    )
                    return
                
                # Получаем номер телефона пользователя
                user_phone = self.normalize_phone_number(user.phone or "")
                
                if not user_phone:
                    logger.warning(f"У пользователя {user.id} не указан номер телефона")
                    await update.message.reply_text(
                        "❌ В вашем профиле не указан номер телефона.\n\n"
                        "Пожалуйста, добавьте номер телефона в настройках профиля."
                    )
                    return
                
                # Проверяем совпадение номеров
                if telegram_phone != user_phone:
                    await update.message.reply_text(
                        f"❌ Номер телефона не совпадает!\n\n"
                        f"Номер в Telegram: {telegram_phone}\n"
                        f"Номер в профиле: {user_phone}\n\n"
                        "Пожалуйста, используйте тот же номер телефона, что указан в профиле."
                    )
                    return
                
                # Номера совпадают - помечаем код как использованный
                verification_code.is_used = True
                verification_code.telegram_phone = telegram_phone
                await sync_to_async(verification_code.save)()
                
                # Отправляем подтверждение успешного входа
                await update.message.reply_text(
                    "✅ Вход через Telegram подтвержден!\n\n"
                    "Вы можете вернуться на сайт - вход выполнен автоматически."
                )
                
                logger.info(f"Успешный вход через Telegram для пользователя {user.id}")
                return
            
            # Специальная обработка для QR-регистрации
            if verification_type == 'qr_registration':
                # Для QR-регистрации пользователь и pending_registration могут отсутствовать
                logger.info(f"Обработка QR-регистрации для кода {verification_code.code}")
                # Для QR-кодов мы пока не можем проверить номер телефона,
                # так как регистрация еще не началась
                # Сохраняем номер телефона для будущей проверки
                verification_code.telegram_phone = telegram_phone
                await sync_to_async(verification_code.save)()
                
                # Генерируем код немедленно для QR-регистрации
                if not verification_code.code:
                    logger.info(f"Генерируем код для QR-верификации {verification_code.id}")
                    await sync_to_async(verification_code.save)()
                    await sync_to_async(verification_code.refresh_from_db)()
                
                # Отправляем код
                verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
                code_text = (
                    f"✅ Номер телефона сохранен\!\n\n"
                    f"🔐 Ваш код подтверждения: ||{verification_code.code}||\n\n"
                    f"Введите этот код на сайте для завершения регистрации\.\n\n"
                    f"⏰ Код действителен в течение 10 минут\."
                )
                
                await update.message.reply_text(
                    code_text,
                    parse_mode='MarkdownV2'
                )
                
                logger.info(f"Код {verification_code.code} отправлен для QR-регистрации")
                return

            # Для обычной регистрации проверяем номер телефона
            registered_phone = ""
            if user:
                registered_phone = self.normalize_phone_number(user.phone or "")
            elif pending_registration:
                registered_phone = self.normalize_phone_number(pending_registration.phone or "")
            else:
                await update.message.reply_text(
                    "❌ В вашей регистрации не указан номер телефона.\n\n"
                    "Пожалуйста, укажите номер телефона при регистрации на сайте."
                )
                return
            if not registered_phone:
                logger.warning(f"Зарегистрированный номер телефона пуст для кода {verification_code.id}")
                await update.message.reply_text(
                    "❌ В вашей регистрации не указан номер телефона.\n\n"
                    "Пожалуйста, укажите номер телефона при регистрации на сайте."
                )
                return
                
            if telegram_phone != registered_phone:
                await update.message.reply_text(
                    f"❌ Номер телефона не совпадает!\n\n"
                    f"Номер в Telegram: {telegram_phone}\n"
                    f"Номер при регистрации: {registered_phone}\n\n"
                    "Пожалуйста, используйте тот же номер телефона, что указан при регистрации."
                )
                return
            
            # Номера совпадают - сохраняем номер телефона и генерируем код
            verification_code.telegram_phone = telegram_phone
            await sync_to_async(verification_code.save)()
            
            # Убеждаемся, что код сгенерирован
            if not verification_code.code:
                logger.info(f"Генерируем код для верификации {verification_code.id}")
                await sync_to_async(verification_code.save)()
                await sync_to_async(verification_code.refresh_from_db)()
                
                if not verification_code.code:
                    logger.error(f"Не удалось сгенерировать код для верификации {verification_code.id}")
                    await update.message.reply_text(
                        "❌ Произошла ошибка при генерации кода.\n\n"
                        "Пожалуйста, попробуйте позже."
                    )
                    return
            
            # Отправляем код пользователю
            verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
            code_text = (
                f"✅ Номер телефона подтвержден\!\n\n"
                f"🔐 Ваш код подтверждения: ||{verification_code.code}||\n\n"
                f"Введите этот код на сайте для завершения {verification_type_display.lower()}\.\n\n"
                f"⏰ Код действителен в течение 10 минут\."
            )
            
            await update.message.reply_text(
                code_text,
                parse_mode='MarkdownV2'
            )
            
            logger.info(f"Код {verification_code.code} отправлен пользователю {chat_id} после проверки номера телефона")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке контакта: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Произошла ошибка при проверке номера телефона.\n\n"
                "Пожалуйста, попробуйте позже.",
                reply_markup=ReplyKeyboardRemove()
            )
    
    async def mark_qr_bot_started(self, verification_code: str):
        """Отмечает запуск бота через QR-код"""
        try:
            # Ищем QR-код по коду верификации
            qr_code = await sync_to_async(
                QRCodeScan.objects.filter(
                    verification_code__code=verification_code
                ).first
            )()
            
            if qr_code:
                # Отмечаем запуск бота
                await sync_to_async(qr_code.mark_bot_started)()
                logger.info(f"Запуск бота отмечен для QR-кода {qr_code.qr_id}")
            else:
                logger.warning(f"QR-код не найден для кода верификации {verification_code}")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке запуска бота для QR-кода: {e}")
    
    async def send_login_request(self, chat_id: str, phone_number: str, verification_code: str):
        """Отправка запроса на вход через Telegram"""
        try:
            # Сообщение для отправки
            message = (
                f"🔗 Запрос на вход через Telegram\n\n"
                f"Ваш номер: {phone_number}\n"
                f"Код подтверждения: {verification_code}\n\n"
                "Пожалуйста, подтвердите вход, нажав кнопку ниже."
            )
            
            # Кнопка подтверждения
            keyboard = [
                [InlineKeyboardButton("✅ Подтвердить вход", callback_data=f"login_{verification_code}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Отправка сообщения
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup
            )
            
            logger.info(f"Запрос на вход отправлен в Telegram для пользователя с телефоном {phone_number}")
        except Exception as e:
            logger.error(f"Ошибка при отправке запроса на вход в Telegram: {e}")

        
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.agree_sms_callback, pattern="agree_sms"))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))


# Глобальный экземпляр бота
def get_bot_instance():
    """Получение экземпляра бота (singleton)"""
    global _bot_instance
    
    if _bot_instance is None:
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не настроен в settings")
        
        _bot_instance = TelegramBot(bot_token)
        logger.info("Создан новый экземпляр Telegram бота")
    
    return _bot_instance


async def send_verification_code_to_telegram(chat_id: str, verification_type: str = 'registration'):
    """Функция для отправки кода верификации через бота"""
    bot = get_bot_instance()
    return await bot.send_verification_code(chat_id, verification_type)


async def send_login_request_to_telegram(chat_id: str, phone_number: str, verification_code: str):
    """Функция для отправки запроса на вход через Telegram"""
    try:
        import telegram
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            logger.error("Ошибка: TELEGRAM_BOT_TOKEN не настроен")
            return False
            
        # Создаем отдельный экземпляр бота для отправки сообщений
        bot = telegram.Bot(token=bot_token)
        
        # Создаем клавиатуру с кнопкой для запроса номера телефона
        keyboard = [
            [KeyboardButton("📱 Поделиться номером телефона", request_contact=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        # Отправляем сообщение с запросом на вход
        login_text = (
            f"🔐 Запрос на вход через Telegram\n\n"
            f"📱 Номер телефона с сайта: {phone_number}\n\n"
            f"Для подтверждения входа поделитесь своим номером телефона, "
            f"нажав кнопку ниже. Мы сверим его с номером, указанным на сайте."
        )
        
        await bot.send_message(
            chat_id=int(chat_id),
            text=login_text,
            reply_markup=reply_markup
        )
        
        logger.info(f"Запрос на вход успешно отправлен в chat_id {chat_id} для номера {phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке запроса на вход через Telegram: {e}")
        return False
