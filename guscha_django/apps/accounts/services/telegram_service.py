from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import timedelta
from typing import Optional, Dict, Any, Tuple
import logging
import secrets
import string
from asgiref.sync import async_to_sync

from ..models import TelegramVerificationCode, PendingUserRegistration, User, PasswordResetToken
from ..validators import TelegramValidator
from ..repositories import TelegramRepository, UserRepository
from telegram_bot.bot import send_verification_code_to_telegram

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для управления Telegram-интеграцией"""
    
    def __init__(self):
        self.telegram_repository = TelegramRepository()
        self.user_repository = UserRepository()
        self.telegram_validator = TelegramValidator()
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Нормализация номера телефона"""
        if not phone:
            return None
        # Удаляем все нецифровые символы
        normalized = ''.join(filter(str.isdigit, phone))
        # Если номер начинается с 8, заменяем на 7
        if normalized.startswith('8') and len(normalized) == 11:
            normalized = '7' + normalized[1:]
        # Добавляем + в начало
        if normalized and not normalized.startswith('+'):
            normalized = '+' + normalized
        return normalized
    
    def generate_verification_code_for_user(self, email: str) -> Dict[str, Any]:
        """Генерация кода верификации для пользователя по email"""
        try:
            # Поиск пользователя по email
            user = self.user_repository.get_by_email(email)
            if not user:
                return {
                    'success': False,
                    'error': 'Пользователь не найден'
                }
            
            # Создание кода верификации с номером телефона пользователя
            verification_code = self.create_verification_code(
                telegram_chat_id=None,  # Пустой для веб-регистрации
                verification_type='qr_registration',
                user=user,
                telegram_phone=user.phone
            )
            
            display_code = verification_code.generate_secure_code()
            return {
                'success': True,
                'verification_code': display_code
            }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации кода верификации для {email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка создания кода верификации'
            }
    
    def generate_verification_code(self) -> str:
        """Простая генерация 6-значного кода"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def create_verification_code(
        self, 
        telegram_chat_id: Optional[str], 
        verification_type: str = 'registration',
        user: Optional[User] = None,
        pending_registration: Optional[PendingUserRegistration] = None,
        telegram_phone: Optional[str] = None
    ) -> TelegramVerificationCode:
        """Создание кода верификации"""
        try:
            # Валидация входных данных
            # Для QR-кодов chat_id может быть пустым
            self.telegram_validator.validate_chat_id_optional(telegram_chat_id)
            self.telegram_validator.validate_verification_type(verification_type)
            
            with transaction.atomic():
                # Создание нового кода
                code = self.generate_verification_code()  # Без параметров возвращает строку
                
                # Устанавливаем разное время жизни в зависимости от типа верификации
                current_time = timezone.now()
                if verification_type == 'qr_registration':
                    expires_at = current_time + timedelta(minutes=20)  # 20 минут для QR-регистрации
                    logger.info(f"Установлено время истечения для QR-регистрации: {expires_at} (через 20 минут от {current_time})")
                else:
                    expires_at = current_time + timedelta(minutes=5)   # 5 минут для обычной регистрации
                    logger.info(f"Установлено время истечения для обычной регистрации: {expires_at} (через 5 минут от {current_time})")
                
                logger.info(f"Создание кода верификации с параметрами: code={code}, chat_id='{telegram_chat_id}', expires_at={expires_at}, type={verification_type}")
                
                verification_code = self.telegram_repository.create_verification_code(
                    code=code,
                    telegram_chat_id=telegram_chat_id,
                    expires_at=expires_at,
                    verification_type=verification_type,
                    user=user,
                    pending_registration=pending_registration,
                    telegram_phone=telegram_phone
                )
                
                # Деактивация старых кодов, исключая только что созданный
                self.telegram_repository.deactivate_old_codes(
                    telegram_chat_id, verification_type, exclude_code_id=verification_code.id
                )
                
                logger.info(f"Код верификации создан успешно: ID={verification_code.id}, code={code}, expires_at={verification_code.expires_at}, chat_id='{telegram_chat_id}', type={verification_type}, user={user.id if user else None}, phone={telegram_phone}")
                return verification_code
                
        except ValidationError as e:
            logger.error(f"Ошибка валидации при создании кода верификации: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при создании кода верификации: {e}")
            raise
    
    def send_verification_code(
        self, 
        telegram_chat_id: str, 
        verification_type: str = 'registration',
        user: Optional[User] = None,
        pending_registration: Optional[PendingUserRegistration] = None,
        telegram_phone: Optional[str] = None
    ) -> bool:
        """Отправка кода верификации в Telegram"""
        try:
            # Создание кода верификации
            verification_code = self.create_verification_code(
                telegram_chat_id, verification_type, user, pending_registration, telegram_phone
            )
            
            # Отправка кода через Telegram бота
            display_code = verification_code.generate_secure_code()
            success = async_to_sync(send_verification_code_to_telegram)(
                telegram_chat_id, 
                display_code
            )
            
            if success:
                logger.info(f"Код верификации отправлен в Telegram: {telegram_chat_id}")
            else:
                logger.error(f"Ошибка отправки кода в Telegram: {telegram_chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при отправке кода верификации: {e}")
            raise

    def send_existing_verification_code(
        self, 
        telegram_chat_id: str, 
        verification_code: TelegramVerificationCode
    ) -> bool:
        """Отправка существующего кода верификации в Telegram"""
        try:
            # Отправка кода через Telegram бота
            display_code = verification_code.generate_secure_code()
            success = async_to_sync(send_verification_code_to_telegram)(
                telegram_chat_id, 
                display_code
            )
            
            if success:
                logger.info(f"Существующий код верификации отправлен в Telegram: {telegram_chat_id}")
            else:
                logger.error(f"Ошибка отправки существующего кода в Telegram: {telegram_chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при отправке существующего кода верификации: {e}")
            raise

    def verify_code(
        self, 
        telegram_chat_id: str, 
        code: str, 
        verification_type: str = 'registration'
    ) -> Tuple[bool, Optional[TelegramVerificationCode]]:
        """Верификация кода по chat_id"""
        try:
            # Валидация входных данных
            self.telegram_validator.validate_chat_id(telegram_chat_id)
            self.telegram_validator.validate_verification_code(code)
            
            # Поиск кода верификации
            verification_code = self.telegram_repository.get_active_verification_code(
                telegram_chat_id, code, verification_type
            )
            
            if not verification_code:
                logger.warning(f"Код верификации не найден: {telegram_chat_id}, {code}")
                return False, None
            
            # Проверка срока действия
            if verification_code.is_expired():
                logger.warning(f"Код верификации истек: {telegram_chat_id}, {code}")
                return False, None
            
            # Проверка использования
            if verification_code.is_used:
                logger.warning(f"Код верификации уже использован: {telegram_chat_id}, {code}")
                return False, None
            
            # Отметка кода как использованного
            with transaction.atomic():
                verification_code.is_used = True
                verification_code.used_at = timezone.now()
                verification_code.save()
            
            logger.info(f"Код верификации успешно проверен: {telegram_chat_id}")
            return True, verification_code
            
        except ValidationError as e:
            logger.error(f"Ошибка валидации при проверке кода: {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при проверке кода верификации: {e}")
            raise
    
    def verify_code_by_phone(
        self, 
        verification_code: str, 
        phone_number: Optional[str] = None,
        verification_type: str = 'qr_registration'
    ) -> Dict[str, Any]:
        """Верификация кода по номеру телефона для API"""
        try:
            # Валидация кода
            self.telegram_validator.validate_verification_code(verification_code)
            
            logger.info(f"Поиск кода верификации: {verification_code}, phone: {phone_number}, type: {verification_type}")
            
            # Поиск активного кода верификации
            code_obj = None
            
            # Для QR-регистрации сначала ищем код без привязки к пользователю
            if verification_type == 'qr_registration':
                logger.info(f"Этап 1: Поиск кода без привязки к пользователю")
                codes = TelegramVerificationCode.objects.filter(
                    verification_type=verification_type,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                # Проверяем каждый код с помощью check_code_match
                for code_candidate in codes:
                    logger.info(f"Этап 1: Проверяем код {code_candidate.id}: user={code_candidate.user_id}, pending_registration={code_candidate.pending_registration_id}, phone={code_candidate.pending_registration.phone if code_candidate.pending_registration else 'None'}, telegram_phone={code_candidate.telegram_phone}, chat_id={code_candidate.telegram_chat_id}")
                    if code_candidate.check_code_match(verification_code):
                        code_obj = code_candidate
                        logger.info(f"Этап 1: Найден подходящий код {code_candidate.id}")
                        break
                logger.info(f"Этап 1 результат: {'найден' if code_obj else 'не найден'}")
            
            # Если код не найден и указан номер телефона, ищем по пользователю
            if not code_obj and phone_number:
                logger.info(f"Этап 2: Поиск по пользователю с номером телефона: {phone_number}")
                # Поиск по связанному пользователю через номер телефона
                user = self.user_repository.get_by_phone(phone_number)
                logger.info(f"Пользователь найден: {user.id if user else 'не найден'}")
                if user:
                    codes = TelegramVerificationCode.objects.filter(
                        verification_type=verification_type,
                        is_used=False,
                        expires_at__gt=timezone.now(),
                        user=user
                    )
                    # Проверяем каждый код с помощью check_code_match
                    for code_candidate in codes:
                        logger.info(f"Этап 2: Проверяем код {code_candidate.id}: user={code_candidate.user_id}, pending_registration={code_candidate.pending_registration_id}, phone={code_candidate.pending_registration.phone if code_candidate.pending_registration else 'None'}, telegram_phone={code_candidate.telegram_phone}, chat_id={code_candidate.telegram_chat_id}")
                        if code_candidate.check_code_match(verification_code):
                            # Дополнительная проверка для QR-регистрации
                            if verification_type == 'qr_registration' and code_candidate.pending_registration:
                                pr_phone = self._normalize_phone(code_candidate.pending_registration.phone)
                                if pr_phone and pr_phone != phone_number:
                                    logger.warning(f"Этап 2: Номер телефона не совпадает - pending_registration.phone: {pr_phone}, запрошенный: {phone_number}")
                                    continue
                            code_obj = code_candidate
                            logger.info(f"Этап 2: Найден подходящий код {code_candidate.id}")
                            break
                    logger.info(f"Этап 2 результат: {'найден' if code_obj else 'не найден'}")
                
                # Если не найден по пользователю, ищем по telegram_phone в коде
                if not code_obj:
                    logger.info(f"Этап 3: Поиск по telegram_phone: {phone_number}")
                    codes = TelegramVerificationCode.objects.filter(
                        verification_type=verification_type,
                        is_used=False,
                        expires_at__gt=timezone.now(),
                        telegram_phone=phone_number
                    )
                    # Проверяем каждый код с помощью check_code_match
                for code_candidate in codes:
                    logger.info(f"Этап 3: Проверяем код {code_candidate.id}: user={code_candidate.user_id}, pending_registration={code_candidate.pending_registration_id}, phone={code_candidate.pending_registration.phone if code_candidate.pending_registration else 'None'}, telegram_phone={code_candidate.telegram_phone}, chat_id={code_candidate.telegram_chat_id}")
                    if code_candidate.check_code_match(verification_code):
                        code_obj = code_candidate
                        logger.info(f"Этап 3: Найден подходящий код {code_candidate.id}")
                        break
                logger.info(f"Этап 3 результат: {'найден' if code_obj else 'не найден'}")
            
            # Если код все еще не найден, ищем по pending_registration
            if not code_obj:
                logger.info(f"Этап 4: Поиск по pending_registration")
                codes = TelegramVerificationCode.objects.filter(
                    verification_type=verification_type,
                    is_used=False,
                    expires_at__gt=timezone.now(),
                    pending_registration__isnull=False
                )
                # Проверяем каждый код с помощью check_code_match
                for code_candidate in codes:
                    logger.info(f"Этап 4: Проверяем код {code_candidate.id}: user={code_candidate.user_id}, pending_registration={code_candidate.pending_registration_id}, phone={code_candidate.pending_registration.phone if code_candidate.pending_registration else 'None'}, telegram_phone={code_candidate.telegram_phone}, chat_id={code_candidate.telegram_chat_id}")
                    if code_candidate.check_code_match(verification_code):
                        code_obj = code_candidate
                        logger.info(f"Этап 4: Найден подходящий код {code_candidate.id}")
                        break
                logger.info(f"Этап 4 результат: {'найден' if code_obj else 'не найден'}")
                
                # Если не найден и указан номер телефона, ищем по pending_registration.phone
                if not code_obj and phone_number:
                    logger.info(f"Этап 5: Поиск по pending_registration.phone: {phone_number}")
                    codes = TelegramVerificationCode.objects.filter(
                        verification_type=verification_type,
                        is_used=False,
                        expires_at__gt=timezone.now(),
                        pending_registration__phone=phone_number
                    )
                    # Проверяем каждый код с помощью check_code_match
                    for code_candidate in codes:
                        logger.info(f"Этап 5: Проверяем код {code_candidate.id}: user={code_candidate.user_id}, pending_registration={code_candidate.pending_registration_id}, phone={code_candidate.pending_registration.phone if code_candidate.pending_registration else 'None'}, telegram_phone={code_candidate.telegram_phone}, chat_id={code_candidate.telegram_chat_id}")
                        if code_candidate.check_code_match(verification_code):
                            code_obj = code_candidate
                            logger.info(f"Этап 5: Найден подходящий код {code_candidate.id}")
                            break
                    logger.info(f"Этап 5 результат: {'найден' if code_obj else 'не найден'}")

            if not code_obj:
                logger.warning(f"Код верификации не найден или недействителен: {verification_code}")
                return {
                    'success': False,
                    'error': 'Неверный или истекший код верификации'
                }
            
            # Проверка срока действия (дополнительная проверка)
            if code_obj.is_expired():
                logger.warning(f"Код верификации истек: {verification_code}")
                return {
                    'success': False,
                    'error': 'Код верификации истек'
                }
            
            # Определение пользователя
            user = None
            requires_registration = False
            
            if code_obj.user:
                user = code_obj.user
            elif code_obj.pending_registration:
                # Завершение регистрации для pending_registration
                user = self.complete_telegram_registration(
                    code_obj.pending_registration,
                    code_obj.telegram_chat_id or '',
                    None  # telegram_username не используется при верификации по телефону
                )
            else:
                # Для QR-регистрации без привязанного пользователя или pending_registration
                # возвращаем успешный результат без пользователя
                logger.info(f"Код верификации успешно проверен для QR-регистрации: {verification_code}")
                requires_registration = True
            
            # Финальная пометка кода как использованного - делаем ПОСЛЕ обработки pending_registration
            # чтобы избежать ошибки "save() prohibited to prevent data loss"
            code_obj.verify_code(verification_code)
            
            logger.info(f"Код верификации успешно проверен: {verification_code}")
            
            result = {
                'success': True,
                'user': user,
                'verification_code': {
                    'code': code_obj.code_hash,
                    'is_used': code_obj.is_used,
                    'expires_at': code_obj.expires_at.isoformat() if code_obj.expires_at else None,
                    'created_at': code_obj.created_at.isoformat() if code_obj.created_at else None
                }
            }
            
            # Добавляем requires_registration только если это необходимо
            if requires_registration:
                result['requires_registration'] = True
                
            return result
            
        except ValidationError as e:
            logger.error(f"Ошибка валидации при проверке кода: {e}")
            return {
                'success': False,
                'error': 'Неверный формат кода верификации'
            }
        except Exception as e:
            logger.error(f"Ошибка при проверке кода верификации: {e}")
            return {
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }
    
    def link_telegram_to_user(
        self, 
        user: User, 
        telegram_chat_id: str, 
        telegram_username: Optional[str] = None
    ) -> bool:
        """Привязка Telegram к пользователю"""
        try:
            with transaction.atomic():
                user.telegram_chat_id = telegram_chat_id
                user.telegram_username = telegram_username
                user.is_telegram_verified = True
                user.save()
            
            logger.info(f"Telegram привязан к пользователю: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при привязке Telegram: {e}")
            raise
    
    def unlink_telegram_from_user(self, user: User) -> bool:
        """Отвязка Telegram от пользователя"""
        try:
            with transaction.atomic():
                user.telegram_chat_id = None
                user.telegram_username = None
                user.is_telegram_verified = False
                user.save()
                
                # Деактивация всех кодов верификации
                self.telegram_repository.deactivate_all_user_codes(user)
            
            logger.info(f"Telegram отвязан от пользователя: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отвязке Telegram: {e}")
            raise
    
    def get_user_by_telegram_chat_id(self, telegram_chat_id: str) -> Optional[User]:
        """Получение пользователя по Telegram chat_id"""
        return self.user_repository.get_by_telegram_chat_id(telegram_chat_id)
    
    def complete_telegram_registration(
        self, 
        pending_registration: PendingUserRegistration, 
        telegram_chat_id: str,
        telegram_username: Optional[str] = None
    ) -> User:
        """Завершение регистрации через Telegram"""
        try:
            with transaction.atomic():
                # Создание пользователя из ожидающей записи
                user = self.user_repository.create_user_from_pending(pending_registration)
                
                # Привязка Telegram (только если есть telegram_chat_id)
                if telegram_chat_id:
                    user.telegram_chat_id = telegram_chat_id
                    user.telegram_username = telegram_username or ''
                    user.is_telegram_verified = True
                else:
                    # Для QR-регистрации пользователь верифицирован через Telegram-бота
                    # даже если telegram_chat_id не сохраняется
                    user.is_telegram_verified = True
                    user.telegram_username = ''
                user.save()
                
                # Деактивация всех кодов верификации (только если есть telegram_chat_id)
                if telegram_chat_id:
                    self.telegram_repository.deactivate_old_codes(
                        telegram_chat_id, 'registration', exclude_code_id=None
                    )
                # Для QR-регистрации деактивируем коды по пользователю
                else:
                    # Отмечаем коды как использованные и обнуляем связь с pending_registration перед его удалением
                    verification_codes = TelegramVerificationCode.objects.filter(
                        pending_registration=pending_registration,
                        verification_type='qr_registration'
                    )
                    for code in verification_codes:
                        code.is_used = True
                        code.used_at = timezone.now()
                        code.user = user  # Связываем с созданным пользователем
                        code.pending_registration = None  # Обнуляем связь с pending_registration
                        code.save()
                
                # Удаление ожидающей записи
                pending_registration.delete()
            
            logger.info(f"Регистрация через Telegram завершена: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации через Telegram: {e}")
            raise
    
    def initiate_telegram_password_reset(self, email: str) -> bool:
        """Инициация сброса пароля через Telegram"""
        try:
            user = self.user_repository.get_by_email(email)
            if not user or not user.telegram_chat_id:
                return False
            
            # Отправка кода верификации
            success = self.send_verification_code(
                user.telegram_chat_id, 
                'password_reset', 
                user=user
            )
            
            if success:
                logger.info(f"Инициирован сброс пароля через Telegram: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка при инициации сброса пароля через Telegram: {e}")
            raise
    
    def confirm_telegram_password_reset(
        self, 
        telegram_chat_id: str, 
        code: str, 
        new_password: str
    ) -> bool:
        """Подтверждение сброса пароля через Telegram"""
        try:
            # Проверка кода
            is_valid, verification_code = self.verify_code(
                telegram_chat_id, code, 'password_reset'
            )
            
            if not is_valid or not verification_code or not verification_code.user:
                return False
            
            # Установка нового пароля
            user = verification_code.user
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Пароль сброшен через Telegram: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при сбросе пароля через Telegram: {e}")
            raise
    
    def get_telegram_statistics(self) -> Dict[str, Any]:
        """Получение статистики Telegram-интеграции"""
        return self.telegram_repository.get_telegram_statistics()
    
    def initiate_telegram_login(self, user: User, phone_number: str) -> Dict[str, Any]:
        """Инициация входа через Telegram"""
        try:
            # Проверяем, привязан ли Telegram к аккаунту пользователя
            if not user.telegram_chat_id:
                logger.warning(f"Пользователь {user.id} не имеет привязанного Telegram аккаунта")
                return {
                    'success': False,
                    'error': 'Telegram не привязан к аккаунту. Сначала привяжите Telegram в настройках профиля.'
                }
            
            # Создание кода верификации для входа
            verification_code = self.create_verification_code(
                telegram_chat_id=user.telegram_chat_id,  # Используем chat_id пользователя
                verification_type='login',
                user=user,
                telegram_phone=phone_number
            )
            
            # Генерируем deep link для Telegram бота
            display_code = verification_code.generate_secure_code()
            telegram_bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GuschaBot')
            telegram_deep_link = f"https://t.me/{telegram_bot_username}?start=login_{display_code}"
            
            logger.info(f"Код верификации для входа создан для пользователя {user.id} (code: {display_code})")
            
            return {
                'success': True,
                'message': 'Код верификации создан. Перейдите в Telegram бот для завершения входа.',
                'verification_code': display_code,
                'telegram_link': telegram_deep_link
            }
                
        except Exception as e:
            logger.error(f"Ошибка при инициации входа через Telegram: {e}")
            return {
                'success': False,
                'error': 'Ошибка инициации входа через Telegram'
            }
    
    def initiate_authenticated_password_reset(self, user: User, request) -> Dict[str, Any]:
        """Инициация сброса пароля для авторизованного пользователя"""
        try:
            # Проверяем, привязан ли Telegram к аккаунту
            if not user.telegram_chat_id:
                return {
                    'success': False,
                    'error': 'Telegram не привязан к аккаунту. Сначала привяжите Telegram в настройках профиля.'
                }
            
            # Получаем информацию о запросе
            from ..utils import SecurityUtils
            request_ip = SecurityUtils.get_client_ip(request) if request else ''
            user_agent = SecurityUtils.get_user_agent(request) if request else ''
            
            # Создаем токен сброса пароля
            reset_token = PasswordResetToken.objects.create(
                user=user,
                ip_address=request_ip,
                user_agent=user_agent
            )
            
            # Генерируем безопасную ссылку на React приложение
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost')
            reset_url = f"{frontend_url}/telegram-reset-password?token={reset_token.token}"
            
            # Отправляем ссылку через Telegram
            from telegram_bot.bot import send_password_reset_link_to_telegram
            success = async_to_sync(send_password_reset_link_to_telegram)(
                user.telegram_chat_id,
                reset_url,
                user.first_name or user.email
            )
            
            if success:
                logger.info(f"Ссылка сброса пароля отправлена пользователю {user.email} через Telegram")
                return {
                    'success': True,
                    'message': 'Ссылка для сброса пароля отправлена в ваш Telegram',
                    'token_id': str(reset_token.id)
                }
            else:
                # Если не удалось отправить, удаляем токен
                reset_token.delete()
                return {
                    'success': False,
                    'error': 'Ошибка отправки ссылки в Telegram'
                }
                
        except Exception as e:
            logger.error(f"Ошибка при инициации сброса пароля для пользователя {user.email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка инициации сброса пароля'
            }
    
    def confirm_password_reset_with_token(self, token: str, new_password: str) -> Dict[str, Any]:
        """Подтверждение сброса пароля по токену"""
        try:
            # Поиск токена
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
            except PasswordResetToken.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Недействительная ссылка для сброса пароля'
                }
            
            # Проверка валидности токена
            if not reset_token.is_valid():
                return {
                    'success': False,
                    'error': 'Ссылка для сброса пароля истекла или уже была использована'
                }
            
            # Установка нового пароля
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Отмечаем токен как использованный
            reset_token.mark_as_used()
            
            logger.info(f"Пароль успешно сброшен для пользователя {user.email} по токену")
            return {
                'success': True,
                'message': 'Пароль успешно изменен'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при сбросе пароля по токену {token}: {e}")
            return {
                'success': False,
                'error': 'Ошибка при смене пароля'
            }
    
    def cleanup_expired_codes(self) -> int:
        """Очистка истекших кодов верификации"""
        try:
            count = self.telegram_repository.cleanup_expired_codes()
            logger.info(f"Удалено {count} истекших кодов верификации")
            return count
        except Exception as e:
            logger.error(f"Ошибка при очистке истекших кодов: {e}")
            raise
    
    def send_phone_change_code(self, user: User, verification_type: str = 'phone_change_current') -> Dict[str, Any]:
        """Отправка кода для подтверждения смены номера телефона"""
        try:
            # Проверяем, привязан ли Telegram к аккаунту
            if not user.telegram_chat_id:
                return {
                    'success': False,
                    'error': 'Telegram не привязан к аккаунту. Сначала привяжите Telegram в настройках профиля.'
                }
            
            # Создание кода верификации
            verification_code = self.create_verification_code(
                telegram_chat_id=user.telegram_chat_id,
                verification_type=verification_type,
                user=user,
                telegram_phone=user.phone
            )
            
            # Отправка кода через Telegram бота
            display_code = verification_code.generate_secure_code()
            from telegram_bot.bot import send_phone_change_code_to_telegram
            success = async_to_sync(send_phone_change_code_to_telegram)(
                user.telegram_chat_id,
                display_code,
                user.phone or '',
                verification_type
            )
            
            if success:
                logger.info(f"Код смены номера отправлен пользователю {user.email} через Telegram")
                return {
                    'success': True,
                    'message': 'Код отправлен в ваш Telegram бот'
                }
            else:
                return {
                    'success': False,
                    'error': 'Ошибка отправки кода в Telegram'
                }
                
        except Exception as e:
            logger.error(f"Ошибка при отправке кода смены номера для пользователя {user.email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка отправки кода'
            }
    
    def verify_phone_change_code(self, user: User, verification_code: str, verification_type: str = 'phone_change_current') -> Dict[str, Any]:
        """Проверка кода для смены номера телефона"""
        try:
            # Валидация кода
            self.telegram_validator.validate_verification_code(verification_code)
            
            # Поиск активных кодов для этого пользователя
            codes = TelegramVerificationCode.objects.filter(
                user=user,
                verification_type=verification_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            # Проверяем каждый код с помощью check_code_match
            code_obj = None
            for code_candidate in codes:
                if code_candidate.check_code_match(verification_code):
                    code_obj = code_candidate
                    break
            
            if not code_obj:
                logger.warning(f"Код верификации не найден для пользователя {user.email}, код: {verification_code}, тип: {verification_type}")
                return {
                    'success': False,
                    'error': 'Неверный или истекший код верификации'
                }
            
            # Отмечаем код как использованный
            with transaction.atomic():
                code_obj.is_used = True
                code_obj.used_at = timezone.now()
                code_obj.save()
            
            logger.info(f"Код смены номера успешно проверен для пользователя {user.email}")
            return {
                'success': True,
                'message': 'Код успешно проверен'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке кода смены номера для пользователя {user.email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка проверки кода'
            }
    
    def initiate_phone_change(self, user: User, new_phone_number: str) -> Dict[str, Any]:
        """Инициация смены номера телефона через Telegram"""
        try:
            # Проверяем, привязан ли Telegram к аккаунту
            if not user.telegram_chat_id:
                return {
                    'success': False,
                    'error': 'Telegram не привязан к аккаунту. Сначала привяжите Telegram в настройках профиля.'
                }
            
            # Создание кода верификации для смены номера
            verification_code = self.create_verification_code(
                telegram_chat_id=user.telegram_chat_id,
                verification_type='phone_change_new',
                user=user,
                telegram_phone=new_phone_number  # Сохраняем новый номер
            )
            
            # Генерируем deep link для Telegram бота
            display_code = verification_code.generate_secure_code()
            telegram_bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GuschaBot')
            telegram_deep_link = f"https://t.me/{telegram_bot_username}?start=phone_change_{display_code}"
            
            logger.info(f"Инициирована смена номера для пользователя {user.email} с {user.phone} на {new_phone_number}")
            
            return {
                'success': True,
                'message': 'Ссылка для подтверждения смены номера создана',
                'telegram_link': telegram_deep_link,
                'verification_code': display_code
            }
                
        except Exception as e:
            logger.error(f"Ошибка при инициации смены номера для пользователя {user.email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка инициации смены номера'
            }
    
    def check_phone_change_status(self, user: User) -> Dict[str, Any]:
        """Проверка статуса смены номера телефона"""
        try:
            # Ищем активный код смены номера
            active_code = self.telegram_repository.get_active_verification_code(
                user.telegram_chat_id,
                'phone_change_new'
            )
            
            if not active_code:
                return {
                    'success': True,
                    'is_completed': False,
                    'message': 'Нет активного запроса на смену номера'
                }
            
            # Проверяем, был ли код использован (т.е. номер подтвержден в Telegram)
            if active_code.is_used:
                # Обновляем номер пользователя
                new_phone = active_code.telegram_phone
                if new_phone and new_phone != user.phone:
                    user.phone = new_phone
                    user.save()
                    
                    # Деактивируем код после успешной смены
                    active_code.is_used = True
                    active_code.save()
                    
                    logger.info(f"Номер телефона успешно изменен для пользователя {user.email} на {new_phone}")
                    
                    return {
                        'success': True,
                        'is_completed': True,
                        'new_phone_number': new_phone
                    }
            
            # Код еще не использован
            return {
                'success': True,
                'is_completed': False,
                'message': 'Ожидание подтверждения в Telegram'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса смены номера для пользователя {user.email}: {e}")
            return {
                'success': False,
                'error': 'Ошибка проверки статуса смены номера'
            }