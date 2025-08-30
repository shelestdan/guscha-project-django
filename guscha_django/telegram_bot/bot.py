import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, CopyTextButton
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
        
        logger.info(f"Команда /start от пользователя {user.first_name} (chat_id: {chat_id})")
        
        # Получаем verification_id из параметров команды
        verification_id = None
        is_login = False
        
        if context.args:
            param = context.args[0]
            logger.info(f"Получен параметр: {param}")
            # Проверяем, это логин или обычная верификация
            if param.startswith('login_'):
                verification_id = param[6:]  # Убираем префикс 'login_'
                is_login = True
                logger.info(f"Обнаружен login параметр: {verification_id}")
            elif param.startswith('phone_change_'):
                # Обработка смены номера телефона
                verification_code = param[13:]  # Убираем префикс 'phone_change_'
                await self.handle_phone_change_start(update, verification_code)
                return
            else:
                verification_id = param
                logger.info(f"Обнаружен обычный параметр: {verification_id}")
        
        # Проверяем, есть ли активный код верификации
        verification_code = None
        is_qr_code = False
        
        if verification_id:
            try:
                logger.info(f"Поиск verification_code для ID: {verification_id}")
                
                # Сначала пытаемся найти QR-код с таким ID (только если это не login)
                qr_code = None
                if not is_login:
                    try:
                        qr_code = await sync_to_async(
                            QRCodeScan.objects.filter(qr_id=verification_id).select_related('verification_code').first
                        )()
                    except Exception as e:
                        logger.debug(f"Ошибка при поиске QR-кода: {e}")
                
                if qr_code:
                    logger.info(f"Найден QR-код: {qr_code.qr_id}")
                    if qr_code.verification_code:
                        qr_verification_code = qr_code.verification_code
                        logger.info(f"Найден связанный verification_code: {qr_verification_code.id}, тип: {qr_verification_code.verification_type}")
                        
                        # Проверяем активность кода верификации
                        if not qr_verification_code.is_used and qr_verification_code.expires_at > timezone.now():
                            verification_code = qr_verification_code
                            is_qr_code = True
                            logger.info(f"QR verification_code активен и будет использован")
                        else:
                            logger.warning(f"QR verification_code неактивен: is_used={qr_verification_code.is_used}, expires_at={qr_verification_code.expires_at}")
                    else:
                        logger.warning(f"QR-код найден, но verification_code отсутствует")
                else:
                    logger.info(f"QR-код с ID {verification_id} не найден, ищем обычный verification_code")
                    
                    # Если QR-код не найден, ищем обычным способом
                    if is_login:
                        # Для login ищем по самому коду, а не по ID
                        logger.info(f"Поиск кода верификации для login: {verification_id}")
                        
                        # Ищем все активные login коды и проверяем соответствие
                        active_login_codes = await sync_to_async(
                            list
                        )(
                            TelegramVerificationCode.objects.filter(
                                verification_type='login',
                                is_used=False,
                                expires_at__gt=timezone.now()
                            ).order_by('-created_at')
                        )
                        
                        for code in active_login_codes:
                            # Проверяем соответствие кода
                            if await sync_to_async(code.check_code_match)(verification_id):
                                verification_code = code
                                logger.info(f"Найден login код: {code.id}")
                                break
                    else:
                        # Для обычной верификации ищем по ID
                        try:
                            verification_id_int = int(verification_id)
                            logger.info(f"Поиск verification_code по ID: {verification_id_int}")
                            
                            verification_code = await sync_to_async(
                                TelegramVerificationCode.objects.filter(
                                    id=verification_id_int,
                                    is_used=False,
                                    expires_at__gt=timezone.now()
                                ).first
                            )()
                            
                            if verification_code:
                                logger.info(f"Найден обычный verification_code: {verification_code.id}, тип: {verification_code.verification_type}")
                            else:
                                logger.warning(f"Обычный verification_code с ID {verification_id_int} не найден или неактивен")
                                
                        except ValueError:
                            logger.warning(f"verification_id {verification_id} не является числом и не найден как QR-код")
                
                if verification_code and not verification_code.is_expired():
                    # Обновляем chat_id в коде верификации
                    verification_code.telegram_chat_id = str(chat_id)
                    await sync_to_async(verification_code.save)()
                    logger.info(f"Обновлен chat_id для verification_code {verification_code.id}")
                    
                    # Проверяем, является ли это QR-кодом
                    if verification_code.verification_type == 'qr_registration':
                        is_qr_code = True
                        logger.info(f"Обнаружен QR-код регистрации")
                        
                        # Пытаемся связать QR-код с существующим пользователем
                        if not verification_code.user:
                            logger.info(f"QR-код {verification_code.id} не связан с пользователем, ищем пользователя с chat_id={chat_id}")
                            try:
                                existing_user = await sync_to_async(
                                    User.objects.filter(telegram_chat_id=str(chat_id)).first
                                )()
                                
                                if existing_user:
                                    verification_code.user = existing_user
                                    await sync_to_async(verification_code.save)()
                                    logger.info(f"QR-код {verification_code.id} успешно связан с пользователем {existing_user.id}")
                                else:
                                    logger.info(f"Пользователь с chat_id={chat_id} не найден, QR-код остается без связи с пользователем")
                            except Exception as e:
                                logger.error(f"Ошибка при связывании QR-кода с пользователем: {e}")
                        else:
                            logger.info(f"QR-код {verification_code.id} уже связан с пользователем {verification_code.user.id}")
                        
                        # Отмечаем запуск бота для QR-кода
                        display_code = await sync_to_async(verification_code.generate_secure_code)()
                        logger.info(f"Сгенерирован код для отображения: {display_code}")
                        await self.mark_qr_bot_started(display_code)
                    
                    # Обновляем пользователя (только если это не регистрация)
                    try:
                        user_obj = await sync_to_async(lambda: verification_code.user)()
                        if user_obj:
                            user_obj.telegram_chat_id = str(chat_id)
                            if user.username:
                                user_obj.telegram_username = user.username
                            await sync_to_async(user_obj.save)()
                            logger.info(f"Обновлен пользователь {user_obj.id} с chat_id {chat_id}")
                    except Exception as e:
                        # Если пользователь не связан - это нормально для некоторых типов верификации
                        logger.debug(f"Пользователь не связан с кодом верификации {verification_id}: {e}")
                    
                    logger.info(f"Связан пользователь {chat_id} с кодом верификации {verification_id}")
                else:
                    verification_code = None
                    logger.warning(f"verification_code не найден или истек для ID: {verification_id}")
            except Exception as e:
                logger.error(f"Ошибка при поиске кода верификации: {e}", exc_info=True)
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
    
    async def handle_phone_change_start(self, update: Update, verification_code: str):
        """Обработка смены номера телефона"""
        chat_id = str(update.effective_chat.id)
        user = update.effective_user
        
        logger.info(f"Обработка смены номера для chat_id={chat_id}, code={verification_code}")
        
        try:
            # Находим код верификации для смены номера
            phone_change_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    verification_type='phone_change_new',
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).order_by('-created_at').first
            )()
            
            if not phone_change_code:
                await update.message.reply_text(
                    "❌ Не найден активный запрос на смену номера.\n\n"
                    "Повторите процедуру смены номера на сайте."
                )
                return
            
            # Проверяем, что код соответствует переданному
            display_code = await sync_to_async(phone_change_code.generate_secure_code)()
            if display_code != verification_code:
                await update.message.reply_text(
                    "❌ Неверная ссылка для смены номера.\n\n"
                    "Повторите процедуру смены номера на сайте."
                )
                return
            
            # Получаем новый номер телефона
            new_phone = phone_change_code.telegram_phone
            
            # Отправляем сообщение с запросом на подтверждение
            welcome_text = (
                f"📱 Смена номера телефона\n\n"
                f"Новый номер: {new_phone}\n\n"
                f"Для подтверждения смены номера необходимо:\n\n"
                f"1. Подтвердить согласие на обработку персональных данных\n"
                f"2. Поделиться номером телефона для сравнения"
            )
            
            # Создаем клавиатуру с кнопкой согласия
            keyboard = [[
                InlineKeyboardButton("✅ Соглашаюсь на обработку данных", callback_data=f"agree_phone_change_{verification_code}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке смены номера: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке запроса.\n\n"
                "Повторите процедуру позже."
            )
    
    async def agree_sms_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик согласия на SMS"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.from_user.id
        username = query.from_user.username
        
        logger.info(f"agree_sms_callback: Начинаем поиск кода для chat_id={chat_id}, username={username}")
        logger.info(f"agree_sms_callback: Используем новую логику поиска: 1) по chat_id, 2) по пользователю, 3) через QRCodeScan")
        
        try:
            verification_code = None
            
            # Сначала пробуем найти по chat_id (для обычной регистрации)
            logger.info(f"agree_sms_callback: Шаг 1 - Ищем код по telegram_chat_id={chat_id}")
            
            # Получаем все коды по chat_id для детального логирования
            all_chat_codes = await sync_to_async(
                list
            )(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=str(chat_id)
                ).order_by('-created_at')
            )
            
            logger.info(f"agree_sms_callback: Всего кодов для chat_id={chat_id}: {len(all_chat_codes)}")
            for code in all_chat_codes:
                logger.info(f"agree_sms_callback: Код {code.id}: user={code.user_id}, type={code.verification_type}, is_used={code.is_used}, expires_at={code.expires_at}, chat_id={code.telegram_chat_id}")
            
            # Ищем активные коды
            active_chat_codes = await sync_to_async(
                list
            )(
                TelegramVerificationCode.objects.filter(
                    telegram_chat_id=str(chat_id),
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).order_by('-created_at')
            )
            
            logger.info(f"agree_sms_callback: Активных кодов для chat_id={chat_id}: {len(active_chat_codes)}")
            for code in active_chat_codes:
                logger.info(f"agree_sms_callback: Активный код {code.id}: user={code.user_id}, type={code.verification_type}, expires_at={code.expires_at}")
            
            verification_code = active_chat_codes[0] if active_chat_codes else None
            
            if verification_code:
                logger.info(f"agree_sms_callback: Найден код по chat_id: {verification_code.id}, тип: {verification_code.verification_type}")
            
            # Если не найден, ищем код входа для пользователя с этим chat_id
            if not verification_code:
                logger.info(f"agree_sms_callback: Шаг 2 - Код по chat_id не найден, ищем пользователя с chat_id={chat_id}")
                # Ищем пользователя с этим chat_id
                user_with_chat_id = await sync_to_async(
                    User.objects.filter(telegram_chat_id=str(chat_id)).first
                )()
                
                if user_with_chat_id:
                    logger.info(f"agree_sms_callback: Найден пользователь {user_with_chat_id.id}, ищем код входа")
                    
                    # Получаем все коды входа для детального логирования
                    all_login_codes = await sync_to_async(
                        list
                    )(
                        TelegramVerificationCode.objects.filter(
                            user=user_with_chat_id,
                            verification_type='login'
                        ).order_by('-created_at')
                    )
                    
                    logger.info(f"agree_sms_callback: Всего кодов входа для пользователя {user_with_chat_id.id}: {len(all_login_codes)}")
                    for code in all_login_codes:
                        logger.info(f"agree_sms_callback: Код входа {code.id}: user={code.user_id}, is_used={code.is_used}, expires_at={code.expires_at}, chat_id={code.telegram_chat_id}")
                    
                    # Ищем активный код входа для этого пользователя
                    active_login_codes = await sync_to_async(
                        list
                    )(
                        TelegramVerificationCode.objects.filter(
                            user=user_with_chat_id,
                            verification_type='login',
                            is_used=False,
                            expires_at__gt=timezone.now()
                        ).order_by('-created_at')
                    )
                    
                    logger.info(f"agree_sms_callback: Активных кодов входа: {len(active_login_codes)}")
                    for code in active_login_codes:
                        logger.info(f"agree_sms_callback: Активный код входа {code.id}: expires_at={code.expires_at}, chat_id={code.telegram_chat_id}")
                    
                    verification_code = active_login_codes[0] if active_login_codes else None
                    
                    if verification_code:
                        logger.info(f"agree_sms_callback: Найден код входа: {verification_code.id}")
                else:
                    logger.info(f"agree_sms_callback: Пользователь с chat_id={chat_id} не найден")
            
            # Если все еще не найден, ищем QR-коды по связанному пользователю
            if not verification_code and user_with_chat_id:
                logger.info(f"agree_sms_callback: Ищем QR-коды типа 'qr_registration' для пользователя {user_with_chat_id.id}")
                
                # Сначала получаем все коды для детального логирования
                all_user_codes = await sync_to_async(
                    list
                )(
                    TelegramVerificationCode.objects.filter(
                        user=user_with_chat_id
                    ).order_by('-created_at')
                )
                
                logger.info(f"agree_sms_callback: Всего кодов для пользователя {user_with_chat_id.id}: {len(all_user_codes)}")
                for code in all_user_codes:
                    logger.info(f"agree_sms_callback: Код {code.id}: user={code.user_id}, type={code.verification_type}, is_used={code.is_used}, expires_at={code.expires_at}, chat_id={code.telegram_chat_id}")
                
                # Теперь ищем активные QR-коды
                qr_codes = await sync_to_async(
                    list
                )(
                    TelegramVerificationCode.objects.filter(
                        user=user_with_chat_id,
                        verification_type='qr_registration',
                        is_used=False,
                        expires_at__gt=timezone.now()
                    ).order_by('-created_at')
                )
                
                logger.info(f"agree_sms_callback: Найдено активных QR-кодов 'qr_registration': {len(qr_codes)}")
                for code in qr_codes:
                    logger.info(f"agree_sms_callback: Активный QR-код {code.id}: user={code.user_id}, chat_id={code.telegram_chat_id}, expires_at={code.expires_at}")
                
                verification_code = qr_codes[0] if qr_codes else None
                
                if verification_code:
                    logger.info(f"agree_sms_callback: Найден QR-код для пользователя: {verification_code.id}")
                    # Обновляем chat_id если он отличается
                    if verification_code.telegram_chat_id != str(chat_id):
                        verification_code.telegram_chat_id = str(chat_id)
                        await sync_to_async(verification_code.save)()
                        logger.info(f"agree_sms_callback: Обновлен chat_id для QR-кода {verification_code.id}")
                else:
                    logger.warning(f"agree_sms_callback: QR-коды для пользователя {user_with_chat_id.id} не найдены")
                    
                    # Дополнительный поиск всех типов кодов для пользователя
                    logger.info(f"agree_sms_callback: Ищем коды любого типа для пользователя {user_with_chat_id.id}")
                    any_codes = await sync_to_async(
                        list
                    )(
                        TelegramVerificationCode.objects.filter(
                            user=user_with_chat_id,
                            is_used=False,
                            expires_at__gt=timezone.now()
                        ).order_by('-created_at')
                    )
                    
                    logger.info(f"agree_sms_callback: Найдено активных кодов любого типа: {len(any_codes)}")
                    for code in any_codes:
                        logger.info(f"agree_sms_callback: Активный код {code.id}: type={code.verification_type}, chat_id={code.telegram_chat_id}")
                    
                    if any_codes:
                        verification_code = any_codes[0]
                        logger.info(f"agree_sms_callback: Используем код {verification_code.id} типа {verification_code.verification_type}")
            elif not verification_code:
                # Дополнительный поиск QR-кодов без привязки к пользователю (для QR-регистрации)
                logger.info(f"agree_sms_callback: Шаг 3 - Ищем QR-коды типа 'qr_registration' без пользователя для chat_id={chat_id}")
                verification_code = await sync_to_async(
                    TelegramVerificationCode.objects.filter(
                        telegram_chat_id=str(chat_id),
                        verification_type='qr_registration',
                        user__isnull=True,
                        is_used=False,
                        expires_at__gt=timezone.now()
                    ).order_by('-created_at').first
                )()
                
                if verification_code:
                    logger.info(f"agree_sms_callback: Найден QR-код без пользователя: {verification_code.id}")
                else:
                    logger.info(f"agree_sms_callback: QR-коды без пользователя не найдены, пробуем через QRCodeScan")
                    # Дополнительный поиск через QRCodeScan для случаев, когда пользователь не найден напрямую
                    logger.info(f"agree_sms_callback: Шаг 4 - Ищем QR-коды через QRCodeScan для chat_id={chat_id}")
                    qr_scan = await sync_to_async(
                        QRCodeScan.objects.filter(
                            verification_code__telegram_chat_id=str(chat_id),
                            verification_code__verification_type='qr_registration',
                            verification_code__is_used=False,
                            verification_code__expires_at__gt=timezone.now()
                        ).select_related('verification_code').first
                    )()
                    
                    if qr_scan and qr_scan.verification_code:
                        verification_code = qr_scan.verification_code
                        logger.info(f"agree_sms_callback: Найден QR-код через QRCodeScan: {verification_code.id}")
                    else:
                        logger.warning(f"agree_sms_callback: QR-коды через QRCodeScan не найдены для chat_id={chat_id}")
            
            # Финальный fallback поиск - любой активный код для данного chat_id
            if not verification_code:
                logger.info(f"agree_sms_callback: Шаг 5 (fallback) - Ищем любой активный код для chat_id={chat_id}")
                fallback_codes = await sync_to_async(
                    list
                )(
                    TelegramVerificationCode.objects.filter(
                        telegram_chat_id=str(chat_id),
                        is_used=False,
                        expires_at__gt=timezone.now()
                    ).order_by('-created_at')
                )
                
                logger.info(f"agree_sms_callback: Найдено fallback кодов: {len(fallback_codes)}")
                for code in fallback_codes:
                    logger.info(f"agree_sms_callback: Fallback код {code.id}: user={code.user_id}, type={code.verification_type}, expires_at={code.expires_at}")
                
                if fallback_codes:
                    verification_code = fallback_codes[0]
                    logger.info(f"agree_sms_callback: Используем fallback код {verification_code.id} типа {verification_code.verification_type}")
            
            if not verification_code:
                logger.error(f"agree_sms_callback: Активный код верификации не найден для chat_id={chat_id}")
                await query.edit_message_text(
                    "❌ Активный код верификации не найден.\n\n"
                    "Пожалуйста, сначала зарегистрируйтесь на сайте."
                )
                return
                
            if verification_code.is_expired():
                logger.warning(f"agree_sms_callback: Код верификации {verification_code.id} истек")
                await query.edit_message_text(
                    "⏰ Код верификации истек.\n\n"
                    "Пожалуйста, повторите процесс регистрации на сайте."
                )
                return
            
            logger.info(f"agree_sms_callback: Найден активный код {verification_code.id}, тип: {verification_code.verification_type}")
            
            # Специальная обработка для QR-регистрации
            if verification_code.verification_type == 'qr_registration':
                logger.info(f"agree_sms_callback: Обрабатываем QR-регистрацию для кода {verification_code.id}")
            
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
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).order_by('-created_at').first
            )()
            
            if not verification_code or verification_code.is_expired():
                return None
                
            # Отправляем сообщение с кодом
            verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
            display_code = await sync_to_async(verification_code.generate_secure_code)()
            code_text = (
                f"🔐 Ваш код подтверждения: ||{display_code}||\n\n"
                f"Введите этот код на сайте для завершения {verification_type_display.lower()}\.\n\n"
                f"⏰ Код действителен в течение 10 минут\."
            )
            
            # Создаем кнопку для копирования кода
            keyboard = InlineKeyboardMarkup([
                [CopyTextButton("📋 Скопировать код", copy_text=display_code)]
            ])
            
            await self.application.bot.send_message(
                chat_id=int(chat_id),
                text=code_text,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            
            return display_code
            
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
                
            if verification_code.is_expired():
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
                # Для QR-регистрации проверяем номер телефона из pending_registration
                display_code = await sync_to_async(verification_code.generate_secure_code)()
                logger.info(f"Обработка QR-регистрации для кода {display_code}")
                
                # Проверяем номер телефона из pending_registration
                expected_phone = ""
                if pending_registration and pending_registration.phone:
                    expected_phone = self.normalize_phone_number(pending_registration.phone)
                    logger.info(f"Ожидаемый номер из pending_registration: {expected_phone}")
                    logger.info(f"Номер из Telegram: {telegram_phone}")
                    
                    # Проверяем совпадение номеров
                    if expected_phone and telegram_phone != expected_phone:
                        await update.message.reply_text(
                            f"❌ Номер телефона не совпадает!\n\n"
                            f"Номер в Telegram: {telegram_phone}\n"
                            f"Номер при регистрации: {expected_phone}\n\n"
                            "Пожалуйста, используйте тот же номер телефона, что указан при регистрации."
                        )
                        return
                
                # Сохраняем номер телефона
                verification_code.telegram_phone = telegram_phone
                await sync_to_async(verification_code.save)()
                
                # Отправка кода пользователю для верификации на фронтенде
                if not display_code:
                    logger.info(f"Генерируем код для QR-верификации {verification_code.id}")
                    display_code = await sync_to_async(verification_code.generate_secure_code)()
                
                # Отправка кода пользователю для верификации на фронтенде
                logger.info(f"Код {display_code} отправлен пользователю для финальной верификации на фронтенде")
                logger.info(f"Код {verification_code.id} остаётся активным до завершения верификации"),
                logger.info(f"Код {verification_code.id} сгенерирован для QR-регистрации и остается активным для верификации")
                
                # Отправляем код
                verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
                code_text = (
                    f"✅ Номер телефона сохранен\!\n\n"
                    f"🔐 Ваш код подтверждения: ||{display_code}||\n\n"
                    f"Введите этот код на сайте для завершения регистрации\.\n\n"
                    f"⏰ Код действителен в течение 10 минут\."
                )
                
                # Создаем inline кнопку для копирования кода
                copy_button = InlineKeyboardButton(
                    text="📋 Скопировать код",
                    copy_text=CopyTextButton(text=display_code)
                )
                keyboard = InlineKeyboardMarkup([[copy_button]])
                
                await update.message.reply_text(
                    code_text,
                    parse_mode='MarkdownV2',
                    reply_markup=keyboard
                )
                
                logger.info(f"Код {display_code} отправлен для QR-регистрации")
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
            
            # Генерируем безопасный код для отображения
            display_code = await sync_to_async(verification_code.generate_secure_code)()
            if not display_code:
                logger.error(f"Не удалось сгенерировать код для верификации {verification_code.id}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при генерации кода.\n\n"
                    "Пожалуйста, попробуйте позже."
                )
                return
            
            # Помечаем код как использованный после успешной генерации
            verification_code.is_used = True
            verification_code.used_at = timezone.now()
            await sync_to_async(verification_code.save)()
            logger.info(f"Код {verification_code.id} помечен как использованный после генерации SMS для обычной регистрации")
            
            # Отправляем код пользователю
            verification_type_display = await sync_to_async(verification_code.get_verification_type_display)()
            code_text = (
                f"✅ Номер телефона подтвержден\!\n\n"
                f"🔐 Ваш код подтверждения: ||{display_code}||\n\n"
                f"Введите этот код на сайте для завершения {verification_type_display.lower()}\.\n\n"
                f"⏰ Код действителен в течение 10 минут\."
            )
            
            # Создаем inline кнопку для копирования кода
            copy_button = InlineKeyboardButton(
                text="📋 Скопировать код",
                copy_text=CopyTextButton(text=display_code)
            )
            keyboard = InlineKeyboardMarkup([[copy_button]])
            
            await update.message.reply_text(
                code_text,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
            
            logger.info(f"Код {display_code} отправлен пользователю {chat_id} после проверки номера телефона")
            
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
            logger.info(f"Отметка запуска бота для кода: {verification_code}")
            
            # Ищем все QR-коды с активными кодами верификации
            qr_codes = await sync_to_async(
                lambda: list(QRCodeScan.objects.filter(
                    verification_code__is_used=False,
                    verification_code__expires_at__gt=timezone.now()
                ).select_related('verification_code'))
            )()
            
            logger.info(f"Найдено {len(qr_codes)} активных QR-кодов для проверки")
            
            # Проверяем каждый QR-код на соответствие коду
            for i, qr_code in enumerate(qr_codes):
                logger.debug(f"Проверяем QR-код {i+1}/{len(qr_codes)}: {qr_code.qr_id}")
                
                if qr_code.verification_code:
                    logger.debug(f"QR-код {qr_code.qr_id} имеет verification_code: {qr_code.verification_code.id}")
                    
                    # Используем check_code_match вместо verify_code, чтобы не помечать код как использованный
                    is_valid = await sync_to_async(lambda vc=qr_code.verification_code, code=verification_code: vc.check_code_match(code))()
                    logger.debug(f"Результат проверки кода для QR {qr_code.qr_id}: {is_valid}")
                    logger.info(f"Код {qr_code.verification_code.id} НЕ помечен как использованный в mark_qr_bot_started (используется check_code_match)")
                    
                    if is_valid:
                        logger.info(f"Найден подходящий QR-код: {qr_code.qr_id}")
                        # Отмечаем запуск бота
                        await sync_to_async(qr_code.mark_bot_started)()
                        logger.info(f"Запуск бота отмечен для QR-кода {qr_code.qr_id}")
                        return
                else:
                    logger.warning(f"QR-код {qr_code.qr_id} не имеет связанного verification_code")
            
            logger.warning(f"QR-код не найден для кода верификации {verification_code} среди {len(qr_codes)} активных QR-кодов")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке запуска бота для QR-кода: {e}", exc_info=True)
    
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
        self.application.add_handler(CallbackQueryHandler(self.agree_phone_change_callback, pattern="agree_phone_change_.*"))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
    
    async def agree_phone_change_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик согласия на смену номера телефона"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.from_user.id
        callback_data = query.data
        
        # Извлекаем код верификации из callback_data
        verification_code = callback_data.replace('agree_phone_change_', '')
        
        logger.info(f"agree_phone_change_callback: Согласие на смену номера от chat_id={chat_id}, code={verification_code}")
        
        try:
            # Находим код верификации
            phone_change_code = await sync_to_async(
                TelegramVerificationCode.objects.filter(
                    verification_type='phone_change_new',
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).order_by('-created_at').first
            )()
            
            if not phone_change_code:
                await query.edit_message_text(
                    "❌ Не найден активный запрос на смену номера.\n\n"
                    "Повторите процедуру смены номера на сайте."
                )
                return
            
            # Проверяем соответствие кода
            display_code = await sync_to_async(phone_change_code.generate_secure_code)()
            if display_code != verification_code:
                await query.edit_message_text(
                    "❌ Неверный код верификации.\n\n"
                    "Повторите процедуру смены номера."
                )
                return
            
            # Обновляем chat_id в коде верификации
            phone_change_code.telegram_chat_id = str(chat_id)
            await sync_to_async(phone_change_code.save)()
            
            # Запрашиваем контакт пользователя
            contact_keyboard = KeyboardButton("📱 Поделиться номером телефона", request_contact=True)
            reply_markup = ReplyKeyboardMarkup([[contact_keyboard]], one_time_keyboard=True, resize_keyboard=True)
            
            await query.edit_message_text(
                "📱 Теперь поделитесь вашим номером телефона.\n\n"
                "Мы сверим его с новым номером, указанным на сайте.",
                reply_markup=None
            )
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text="👇 Нажмите кнопку для подтверждения номера телефона:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке согласия на смену номера: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка.\n\n"
                "Повторите процедуру позже."
            )


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


async def send_phone_change_code_to_telegram(chat_id: str, verification_code: str, current_phone: str, verification_type: str):
    """Функция для отправки кода смены номера телефона через Telegram"""
    try:
        import telegram
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            logger.error("Ошибка: TELEGRAM_BOT_TOKEN не настроен")
            return False
            
        # Создаем отдельный экземпляр бота для отправки сообщений
        bot = telegram.Bot(token=bot_token)
        
        # Определяем текст сообщения в зависимости от типа верификации
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
        
        await bot.send_message(
            chat_id=int(chat_id),
            text=message_text
        )
        
        logger.info(f"Код смены номера успешно отправлен в chat_id {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке кода смены номера через Telegram: {e}")
        return False


async def send_password_reset_link_to_telegram(chat_id: str, reset_url: str, user_name: str):
    """Функция для отправки ссылки сброса пароля через Telegram"""
    try:
        import telegram
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if not bot_token:
            logger.error("Ошибка: TELEGRAM_BOT_TOKEN не настроен")
            return False
            
        # Создаем отдельный экземпляр бота для отправки сообщений
        bot = telegram.Bot(token=bot_token)
        
        # Создаем клавиатуру с кнопкой для перехода по ссылке
        keyboard = [[
            InlineKeyboardButton("🔐 Сбросить пароль", url=reset_url)
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение со ссылкой сброса пароля
        reset_text = (
            f"🔐 Сброс пароля\n\n"
            f"Привет, {user_name}!\n\n"
            f"Вы запросили сброс пароля для вашего аккаунта. "
            f"Нажмите кнопку ниже, чтобы установить новый пароль.\n\n"
            f"⚠️ Ссылка действительна в течение 1 часа.\n\n"
            f"Если вы не запрашивали сброс пароля, просто проигнорируйте это сообщение."
        )
        
        await bot.send_message(
            chat_id=int(chat_id),
            text=reset_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"Ссылка сброса пароля успешно отправлена в chat_id {chat_id} для пользователя {user_name}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке ссылки сброса пароля через Telegram: {e}")
        return False
