"""Сервис для работы с номерами телефонов."""

import logging
from typing import Optional, Tuple, Dict, Any

from ..utils.validators import PhoneValidator, ValidationResult
from ..utils.formatters import PhoneFormatter
from ..utils.helpers import hash_phone_number
from ..exceptions import PhoneValidationError, ValidationError

logger = logging.getLogger(__name__)


class PhoneService:
    """Сервис для работы с номерами телефонов."""
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Нормализует номер телефона."""
        try:
            return PhoneValidator.normalize_phone(phone)
        except Exception as e:
            logger.error(f"Ошибка нормализации номера телефона: {e}")
            raise PhoneValidationError(f"Ошибка нормализации номера: {e}")
    
    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """Валидирует номер телефона."""
        try:
            return PhoneValidator.validate_phone(phone)
        except Exception as e:
            logger.error(f"Ошибка валидации номера телефона: {e}")
            raise PhoneValidationError(f"Ошибка валидации номера: {e}")
    
    @staticmethod
    def validate_phone_match(phone1: str, phone2: str) -> ValidationResult:
        """Проверяет совпадение двух номеров телефона."""
        try:
            return PhoneValidator.validate_phone_match(phone1, phone2)
        except Exception as e:
            logger.error(f"Ошибка сравнения номеров телефона: {e}")
            raise PhoneValidationError(f"Ошибка сравнения номеров: {e}")
    
    @staticmethod
    def format_for_display(phone: str) -> str:
        """Форматирует номер телефона для отображения."""
        try:
            return PhoneFormatter.format_for_display(phone)
        except Exception as e:
            logger.error(f"Ошибка форматирования номера для отображения: {e}")
            return phone  # Возвращаем исходный номер в случае ошибки
    
    @staticmethod
    def format_for_storage(phone: str) -> str:
        """Форматирует номер телефона для хранения в БД."""
        try:
            return PhoneFormatter.format_for_storage(phone)
        except Exception as e:
            logger.error(f"Ошибка форматирования номера для хранения: {e}")
            return phone  # Возвращаем исходный номер в случае ошибки
    
    @staticmethod
    def mask_phone_for_logs(phone: str) -> str:
        """Маскирует номер телефона для безопасного логирования."""
        try:
            return PhoneFormatter.mask_phone(phone)
        except Exception as e:
            logger.error(f"Ошибка маскирования номера телефона: {e}")
            return "***"  # Возвращаем маску в случае ошибки
    
    @staticmethod
    def get_phone_hash(phone: str) -> str:
        """Получает хеш номера телефона для логирования."""
        try:
            return hash_phone_number(phone)
        except Exception as e:
            logger.error(f"Ошибка создания хеша номера телефона: {e}")
            return "unknown"
    
    @classmethod
    def process_phone_input(
        cls,
        phone: str,
        context: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Обрабатывает ввод номера телефона с полной валидацией.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (is_valid, normalized_phone, error_message)
        """
        try:
            if not phone or not phone.strip():
                return False, None, "Номер телефона не может быть пустым"
            
            # Валидируем номер
            validation_result = cls.validate_phone(phone.strip())
            
            if validation_result.is_valid:
                phone_hash = cls.get_phone_hash(validation_result.normalized_value)
                logger.info(
                    f"Успешная валидация номера телефона {phone_hash}"
                    f"{f' в контексте {context}' if context else ''}"
                )
                return True, validation_result.normalized_value, None
            else:
                error_message = ", ".join(validation_result.errors)
                logger.warning(
                    f"Неуспешная валидация номера телефона: {error_message}"
                    f"{f' в контексте {context}' if context else ''}"
                )
                return False, None, error_message
                
        except Exception as e:
            logger.error(
                f"Ошибка обработки ввода номера телефона: {e}"
                f"{f' в контексте {context}' if context else ''}"
            )
            return False, None, "Ошибка обработки номера телефона"
    
    @classmethod
    def compare_phones(
        cls,
        phone1: str,
        phone2: str,
        context: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Сравнивает два номера телефона.
        
        Returns:
            Tuple[bool, Optional[str]]: (phones_match, error_message)
        """
        try:
            if not phone1 or not phone2:
                return False, "Один из номеров телефона пуст"
            
            # Валидируем и сравниваем номера
            validation_result = cls.validate_phone_match(phone1.strip(), phone2.strip())
            
            if validation_result.is_valid:
                phone1_hash = cls.get_phone_hash(phone1)
                phone2_hash = cls.get_phone_hash(phone2)
                logger.info(
                    f"Номера телефона совпадают: {phone1_hash} == {phone2_hash}"
                    f"{f' в контексте {context}' if context else ''}"
                )
                return True, None
            else:
                error_message = ", ".join(validation_result.errors)
                phone1_hash = cls.get_phone_hash(phone1)
                phone2_hash = cls.get_phone_hash(phone2)
                logger.warning(
                    f"Номера телефона не совпадают: {phone1_hash} != {phone2_hash}, "
                    f"ошибка: {error_message}"
                    f"{f' в контексте {context}' if context else ''}"
                )
                return False, error_message
                
        except Exception as e:
            logger.error(
                f"Ошибка сравнения номеров телефона: {e}"
                f"{f' в контексте {context}' if context else ''}"
            )
            return False, "Ошибка сравнения номеров телефона"
    
    @classmethod
    def get_phone_info(cls, phone: str) -> Dict[str, Any]:
        """Получает информацию о номере телефона."""
        try:
            validation_result = cls.validate_phone(phone)
            
            info = {
                'original': phone,
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
            }
            
            if validation_result.is_valid:
                normalized = validation_result.normalized_value
                info.update({
                    'normalized': normalized,
                    'display_format': cls.format_for_display(normalized),
                    'storage_format': cls.format_for_storage(normalized),
                    'masked': cls.mask_phone_for_logs(normalized),
                    'hash': cls.get_phone_hash(normalized),
                    'is_russian': normalized.startswith('+7'),
                    'length': len(normalized)
                })
            
            return info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о номере телефона: {e}")
            return {
                'original': phone,
                'is_valid': False,
                'errors': [f"Ошибка обработки: {e}"]
            }
    
    @staticmethod
    def is_russian_phone(phone: str) -> bool:
        """Проверяет, является ли номер российским."""
        try:
            normalized = PhoneValidator.normalize_phone(phone)
            return normalized.startswith('+7')
        except Exception:
            return False
    
    @staticmethod
    def extract_country_code(phone: str) -> Optional[str]:
        """Извлекает код страны из номера телефона."""
        try:
            normalized = PhoneValidator.normalize_phone(phone)
            if normalized.startswith('+'):
                # Для российских номеров
                if normalized.startswith('+7'):
                    return '+7'
                # Для других стран - берем первые 1-3 цифры после +
                for i in range(2, 5):  # +1, +12, +123
                    if len(normalized) > i:
                        return normalized[:i]
            return None
        except Exception as e:
            logger.error(f"Ошибка извлечения кода страны: {e}")
            return None