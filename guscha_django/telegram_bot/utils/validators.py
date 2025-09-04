"""Валидаторы для Telegram бота."""

import re
from dataclasses import dataclass
from typing import Optional, List
from ..exceptions import PhoneValidationError, ValidationError


@dataclass
class ValidationResult:
    """Результат валидации."""
    is_valid: bool
    normalized_value: Optional[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PhoneValidator:
    """Валидатор номеров телефонов."""
    
    # Паттерн для валидации номера телефона
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    
    # Паттерны для нормализации российских номеров
    RUSSIAN_8_PATTERN = re.compile(r'^8(\d{10})$')
    RUSSIAN_7_PATTERN = re.compile(r'^7(\d{10})$')
    
    @classmethod
    def normalize_phone(cls, phone_number: str) -> str:
        """Нормализует номер телефона для сравнения."""
        if not phone_number:
            return ""
        
        # Удаляем все символы кроме цифр и знака +
        normalized = re.sub(r'[^\d+]', '', phone_number)
        
        # Если номер начинается с 8, заменяем на +7 (для российских номеров)
        match = cls.RUSSIAN_8_PATTERN.match(normalized)
        if match:
            normalized = '+7' + match.group(1)
        
        # Если номер начинается с 7 без +, добавляем +
        elif cls.RUSSIAN_7_PATTERN.match(normalized):
            normalized = '+' + normalized
            
        return normalized
    
    @classmethod
    def validate_phone(cls, phone_number: str) -> ValidationResult:
        """Валидирует номер телефона."""
        if not phone_number:
            return ValidationResult(
                is_valid=False,
                errors=["Номер телефона не может быть пустым"]
            )
        
        # Нормализуем номер
        normalized = cls.normalize_phone(phone_number)
        
        if not normalized:
            return ValidationResult(
                is_valid=False,
                errors=["Некорректный формат номера телефона"]
            )
        
        # Проверяем формат
        clean_phone = normalized.replace(' ', '').replace('-', '')
        if not cls.PHONE_PATTERN.match(clean_phone):
            return ValidationResult(
                is_valid=False,
                errors=["Некорректный формат номера телефона"]
            )
        
        # Проверяем длину (международный стандарт E.164)
        if len(clean_phone) < 7 or len(clean_phone) > 15:
            return ValidationResult(
                is_valid=False,
                errors=["Номер телефона должен содержать от 7 до 15 цифр"]
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=normalized
        )
    
    @classmethod
    def validate_phone_match(cls, phone1: str, phone2: str) -> ValidationResult:
        """Проверяет совпадение двух номеров телефона."""
        result1 = cls.validate_phone(phone1)
        result2 = cls.validate_phone(phone2)
        
        if not result1.is_valid:
            return ValidationResult(
                is_valid=False,
                errors=[f"Первый номер некорректен: {', '.join(result1.errors)}"]
            )
        
        if not result2.is_valid:
            return ValidationResult(
                is_valid=False,
                errors=[f"Второй номер некорректен: {', '.join(result2.errors)}"]
            )
        
        if result1.normalized_value != result2.normalized_value:
            return ValidationResult(
                is_valid=False,
                errors=["Номера телефонов не совпадают"]
            )
        
        return ValidationResult(is_valid=True)


class ChatIdValidator:
    """Валидатор chat_id."""
    
    @staticmethod
    def validate_chat_id(chat_id: str) -> ValidationResult:
        """Валидирует chat_id."""
        if not chat_id:
            return ValidationResult(
                is_valid=False,
                errors=["Chat ID не может быть пустым"]
            )
        
        try:
            int(chat_id)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                errors=["Chat ID должен быть числом"]
            )
        
        return ValidationResult(is_valid=True)


class VerificationCodeValidator:
    """Валидатор кодов верификации."""
    
    # Паттерн для кода верификации (6 цифр)
    CODE_PATTERN = re.compile(r'^\d{6}$')
    
    @classmethod
    def validate_code_format(cls, code: str) -> ValidationResult:
        """Валидирует формат кода верификации."""
        if not code:
            return ValidationResult(
                is_valid=False,
                errors=["Код верификации не может быть пустым"]
            )
        
        if not cls.CODE_PATTERN.match(code):
            return ValidationResult(
                is_valid=False,
                errors=["Код верификации должен содержать 6 цифр"]
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=code
        )