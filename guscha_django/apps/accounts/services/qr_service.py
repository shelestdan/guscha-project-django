from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from typing import Optional, Dict, Any, Tuple
import logging
import uuid

from ..models import QRCodeScan, TelegramVerificationCode
from ..validators import QRValidator
from ..repositories import QRRepository, TelegramRepository
from .telegram_service import TelegramService

logger = logging.getLogger(__name__)


class QRService:
    """Сервис для управления QR-кодами"""
    
    def __init__(self):
        self.qr_repository = QRRepository()
        self.telegram_repository = TelegramRepository()
        self.telegram_service = TelegramService()
        self.qr_validator = QRValidator()
    
    def create_qr_code(
        self, 
        base_url: Optional[str] = None,
        bot_username: Optional[str] = None,
        pending_registration_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Создание QR-кода для регистрации"""
        try:
            # Использование настроек по умолчанию
            if not base_url:
                # Используем пустую строку, чтобы использовать относительные пути
                base_url = ''
            if not bot_username:
                bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GuschaBot')
            
            # Получаем pending_registration если передан ID
            pending_registration = None
            if pending_registration_id:
                from ..models import PendingUserRegistration
                try:
                    pending_registration = PendingUserRegistration.objects.get(
                        id=pending_registration_id,
                        expires_at__gt=timezone.now()
                    )
                except PendingUserRegistration.DoesNotExist:
                    logger.warning(f"PendingUserRegistration не найден: {pending_registration_id}")
            
            with transaction.atomic():
                # Создание записи QR-кода
                qr_code = self.qr_repository.create_qr_code()
                
                # Создание кода верификации для QR-регистрации
                telegram_phone = pending_registration.phone if pending_registration else None
                verification_code = self.telegram_service.create_verification_code(
                    telegram_chat_id='',  # Будет заполнено при старте бота
                    verification_type='qr_registration',
                    pending_registration=pending_registration,
                    telegram_phone=telegram_phone
                )
                
                # Связывание QR-кода с кодом верификации и pending_registration
                qr_code.verification_code = verification_code
                qr_code.pending_registration = pending_registration
                qr_code.save()
                
                # Генерация URL-ов
                trigger_url = qr_code.generate_trigger_url(base_url)
                telegram_url = qr_code.generate_telegram_url(bot_username)
                
                # Обновление записи с URL-ами
                qr_code.trigger_url = trigger_url
                qr_code.telegram_bot_url = telegram_url
                qr_code.save()
                
                logger.info(f"Создан QR-код: {qr_code.qr_id}")
                return {
                    'success': True,
                    'qr_code': qr_code
                }
                
        except Exception as e:
            logger.error(f"Ошибка при создании QR-кода: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_qr_trigger(
        self, 
        qr_id: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Обработка триггера QR-кода"""
        try:
            # Валидация QR ID
            self.qr_validator.validate_qr_id(qr_id)
            
            # Поиск QR-кода
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code:
                logger.warning(f"QR-код не найден: {qr_id}")
                return {
                    'success': False,
                    'error': 'QR-код не найден'
                }
            
            # Отметка сканирования
            with transaction.atomic():
                qr_code.mark_scanned(ip_address, user_agent)
                
                # Проверяем, есть ли уже код верификации
                if not qr_code.verification_code:
                    # Получаем номер телефона из pending_registration если есть
                    telegram_phone = None
                    if qr_code.pending_registration:
                        telegram_phone = qr_code.pending_registration.phone
                    
                    # Создание кода верификации для Telegram только если его нет
                    verification_code = self.telegram_service.create_verification_code(
                        telegram_chat_id='',  # Будет заполнено при старте бота
                        verification_type='qr_registration',
                        pending_registration=qr_code.pending_registration,
                        telegram_phone=telegram_phone
                    )
                    
                    # Связывание QR-кода с кодом верификации
                    qr_code.verification_code = verification_code
                    qr_code.save()
                else:
                    # Если код уже есть, просто обновляем URL с существующим кодом
                    bot_username = getattr(settings, 'TELEGRAM_BOT_USERNAME', 'GuschaBot')
                    telegram_url = qr_code.generate_telegram_url(bot_username)
                    qr_code.telegram_bot_url = telegram_url
                    qr_code.save()
            
            logger.info(f"QR-код отсканирован: {qr_id}")
            return {
                'success': True,
                'qr_code': qr_code
            }
            
        except ValidationError as e:
            logger.error(f"Ошибка валидации при обработке QR-триггера: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Ошибка при обработке QR-триггера: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def activate_qr_trigger(self, qr_id: str) -> bool:
        """Активация триггера QR-кода"""
        try:
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code:
                return False

            with transaction.atomic():
                qr_code.mark_trigger_activated()
            
            logger.info(f"Триггер QR-кода активирован: {qr_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при активации триггера QR-кода: {e}")
            raise
    
    def mark_bot_started(
        self, 
        qr_id: str, 
        telegram_chat_id: str
    ) -> Dict[str, Any]:
        """Отметка запуска бота для QR-кода"""
        try:
            # Валидация входных данных
            self.qr_validator.validate_qr_id(qr_id)
            
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code:
                logger.warning(f"QR-код не найден при запуске бота: {qr_id}")
                return {
                    'success': False,
                    'error': 'QR-код не найден'
                }
            
            with transaction.atomic():
                # Отметка запуска бота
                qr_code.mark_bot_started()
                
                # Обновление кода верификации с chat_id
                if qr_code.verification_code:
                    verification_code = qr_code.verification_code
                    verification_code.telegram_chat_id = telegram_chat_id
                    verification_code.save()
                    
                    # Отправка существующего кода верификации
                    self.telegram_service.send_existing_verification_code(
                        telegram_chat_id,
                        verification_code
                    )
                    
                    logger.info(f"Бот запущен для QR-кода: {qr_id}")
                    return {
                        'success': True,
                        'verification_code': verification_code
                    }
            
            return {
                'success': False,
                'error': 'Код верификации не найден'
            }
            
        except ValidationError as e:
            logger.error(f"Ошибка валидации при запуске бота: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Ошибка при запуске бота для QR-кода: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_qr_status(self, qr_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса QR-кода"""
        try:
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code:
                return None
            
            # Проверяем, есть ли код верификации и готов ли он
            verification_code_ready = False
            verification_code_data = None
            
            if qr_code.verification_code:
                verification_code = qr_code.verification_code
                # Код готов, если он сгенерирован и у него есть telegram_phone
                if verification_code.code and hasattr(verification_code, 'telegram_phone') and verification_code.telegram_phone:
                    verification_code_ready = True
                    verification_code_data = {
                        'code': verification_code.code,
                        'is_used': verification_code.is_used,
                        'is_expired': verification_code.is_expired(),
                        'has_telegram_phone': bool(verification_code.telegram_phone)
                    }
            
            return {
                'qr_id': str(qr_code.qr_id),
                'scanned_at': qr_code.scanned_at,
                'trigger_activated_at': qr_code.trigger_activated_at,
                'bot_started_at': qr_code.bot_started_at,
                'scan_count': qr_code.scan_count,
                'successful_activations': qr_code.successful_activations,
                'is_complete_flow': qr_code.is_complete_flow(),
                'created_at': qr_code.created_at,
                'has_verification_code': bool(qr_code.verification_code),
                'verification_code_ready': verification_code_ready,
                'verification_code_data': verification_code_data,
                'verification_code_used': (
                    qr_code.verification_code.is_used 
                    if qr_code.verification_code else False
                )
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса QR-кода: {e}")
            raise
    
    def complete_qr_registration(
        self, 
        qr_id: str, 
        telegram_chat_id: str, 
        code: str,
        user_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Завершение регистрации через QR-код"""
        try:
            # Проверка кода верификации
            is_valid, verification_code = self.telegram_service.verify_code(
                telegram_chat_id, code, 'qr_registration'
            )
            
            if not is_valid or not verification_code:
                return None
            
            # Поиск QR-кода
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code or qr_code.verification_code != verification_code:
                return None
            
            with transaction.atomic():
                # Создание ожидающей регистрации
                from .user_service import UserService
                user_service = UserService()
                
                pending_registration = user_service.create_pending_registration(user_data)
                
                # Завершение регистрации через Telegram
                user = self.telegram_service.complete_telegram_registration(
                    pending_registration,
                    telegram_chat_id
                )
                
                # Обновление статистики QR-кода
                qr_code.successful_activations += 1
                qr_code.save()
            
            logger.info(f"Регистрация через QR-код завершена: {qr_id}")
            return {
                'user_id': user.id,
                'email': user.email,
                'qr_id': str(qr_code.qr_id)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при завершении регистрации через QR-код: {e}")
            raise
    
    def get_qr_statistics(self) -> Dict[str, Any]:
        """Получение статистики QR-кодов"""
        return self.qr_repository.get_qr_statistics()
    
    def cleanup_old_qr_codes(self, days: int = 7) -> int:
        """Очистка старых QR-кодов"""
        try:
            deleted_count = self.qr_repository.cleanup_old_qr_codes(days)
            logger.info(f"Удалено старых QR-кодов: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых QR-кодов: {e}")
            raise
    
    def get_qr_code_by_verification(self, verification_code: TelegramVerificationCode) -> Optional[QRCodeScan]:
        """Получение QR-кода по коду верификации"""
        return self.qr_repository.get_by_verification_code(verification_code)
    
    def validate_qr_flow(self, qr_id: str) -> Dict[str, bool]:
        """Валидация потока QR-кода"""
        try:
            qr_code = self.qr_repository.get_by_qr_id(qr_id)
            if not qr_code:
                return {'valid': False, 'reason': 'QR-код не найден'}
            
            validation_result = {
                'valid': True,
                'scanned': bool(qr_code.scanned_at),
                'trigger_activated': bool(qr_code.trigger_activated_at),
                'bot_started': bool(qr_code.bot_started_at),
                'has_verification_code': bool(qr_code.verification_code),
                'verification_code_valid': False,
                'complete_flow': qr_code.is_complete_flow()
            }
            
            if qr_code.verification_code:
                validation_result['verification_code_valid'] = qr_code.verification_code.is_valid()
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Ошибка при валидации потока QR-кода: {e}")
            return {'valid': False, 'reason': str(e)}