# -*- coding: utf-8 -*-
"""
Расширенные утилиты валидации и санитизации данных.

Обеспечивает:
- Комплексную валидацию различных типов данных
- Защиту от различных типов атак
- Валидацию бизнес-логики
- Проверку целостности данных
"""

import re
import json
import logging
import hashlib
import ipaddress
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.utils.html import escape, strip_tags
from django.conf import settings

logger = logging.getLogger('security')


class AdvancedValidator:
    """
    Расширенный класс для валидации различных типов данных.
    """
    
    # Регулярные выражения для различных типов данных
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'phone': re.compile(r'^\+?[1-9]\d{1,14}$'),
        'username': re.compile(r'^[a-zA-Z0-9_]{3,30}$'),
        'password': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'),
        'url': re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'),
        'ipv4': re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
        'ipv6': re.compile(r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'),
        'mac_address': re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'),
        'credit_card': re.compile(r'^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$'),
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE),
        'slug': re.compile(r'^[-a-zA-Z0-9_]+$'),
        'hex_color': re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$'),
        'base64': re.compile(r'^[A-Za-z0-9+/]*={0,2}$'),
    }
    
    # Опасные паттерны для различных типов атак
    ATTACK_PATTERNS = {
        'sql_injection': [
            re.compile(r"('|(\-\-)|(;)|(\||\|)|(\*|\*))", re.IGNORECASE),
            re.compile(r"\b(union|select|insert|delete|update|drop|create|alter|exec|execute|sp_|xp_)\b", re.IGNORECASE),
            re.compile(r"\b(or|and)\s+\d+\s*=\s*\d+", re.IGNORECASE),
            re.compile(r"\b(or|and)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"]\b", re.IGNORECASE),
        ],
        'xss': [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:\s*", re.IGNORECASE),
            re.compile(r"on\w+\s*=\s*['\"]?[^'\"]*['\"]?", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>", re.IGNORECASE),
            re.compile(r"<object[^>]*>", re.IGNORECASE),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
            re.compile(r"<link[^>]*>", re.IGNORECASE),
            re.compile(r"<meta[^>]*>", re.IGNORECASE),
        ],
        'command_injection': [
            re.compile(r"[;&|`$(){}\[\]]", re.IGNORECASE),
            re.compile(r"\b(cat|ls|pwd|whoami|id|uname|wget|curl|nc|netcat|rm|mv|cp|chmod|chown)\b", re.IGNORECASE),
            re.compile(r"\.\.[\/\\]", re.IGNORECASE),
        ],
        'ldap_injection': [
            re.compile(r"[()&|!*]", re.IGNORECASE),
            re.compile(r"\\[0-9a-f]{2}", re.IGNORECASE),
        ],
        'xpath_injection': [
            re.compile(r"['\"]\s*(or|and)\s*['\"]?", re.IGNORECASE),
            re.compile(r"\bcount\s*\(", re.IGNORECASE),
            re.compile(r"\bstring-length\s*\(", re.IGNORECASE),
        ],
    }
    
    @classmethod
    def validate_string(cls, value: str, 
                       min_length: int = 0, 
                       max_length: int = 10000,
                       pattern: Optional[str] = None,
                       allow_empty: bool = True,
                       sanitize: bool = True) -> str:
        """
        Валидирует строковое значение.
        
        Args:
            value: Значение для валидации
            min_length: Минимальная длина
            max_length: Максимальная длина
            pattern: Регулярное выражение для проверки
            allow_empty: Разрешить пустые строки
            sanitize: Санитизировать значение
        
        Returns:
            Валидированная и санитизированная строка
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(value, str):
            raise ValidationError("Значение должно быть строкой")
        
        # Проверяем пустое значение
        if not value.strip() and not allow_empty:
            raise ValidationError("Значение не может быть пустым")
        
        # Санитизируем если нужно
        if sanitize:
            value = cls.sanitize_string(value)
        
        # Проверяем длину
        if len(value) < min_length:
            raise ValidationError(f"Минимальная длина: {min_length} символов")
        
        if len(value) > max_length:
            raise ValidationError(f"Максимальная длина: {max_length} символов")
        
        # Проверяем паттерн
        if pattern and not re.match(pattern, value):
            raise ValidationError("Значение не соответствует требуемому формату")
        
        # Проверяем на атаки
        cls._check_for_attacks(value)
        
        return value
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Валидирует email адрес.
        
        Args:
            email: Email для валидации
        
        Returns:
            Валидированный email
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(email, str):
            raise ValidationError("Email должен быть строкой")
        
        email = email.strip().lower()
        
        # Проверяем длину
        if len(email) > 254:
            raise ValidationError("Email слишком длинный")
        
        # Проверяем базовый формат
        if not cls.PATTERNS['email'].match(email):
            raise ValidationError("Некорректный формат email")
        
        # Используем встроенный валидатор Django
        try:
            django_validate_email(email)
        except ValidationError:
            raise ValidationError("Некорректный email адрес")
        
        # Проверяем на атаки
        cls._check_for_attacks(email)
        
        # Проверяем домен на подозрительность
        domain = email.split('@')[1]
        if cls._is_suspicious_domain(domain):
            raise ValidationError("Подозрительный домен email")
        
        return email
    
    @classmethod
    def validate_password(cls, password: str, 
                         min_length: int = 8,
                         require_uppercase: bool = True,
                         require_lowercase: bool = True,
                         require_digits: bool = True,
                         require_special: bool = True,
                         check_common: bool = True) -> str:
        """
        Валидирует пароль.
        
        Args:
            password: Пароль для валидации
            min_length: Минимальная длина
            require_uppercase: Требовать заглавные буквы
            require_lowercase: Требовать строчные буквы
            require_digits: Требовать цифры
            require_special: Требовать специальные символы
            check_common: Проверять на распространенные пароли
        
        Returns:
            Валидированный пароль
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(password, str):
            raise ValidationError("Пароль должен быть строкой")
        
        # Проверяем длину
        if len(password) < min_length:
            raise ValidationError(f"Минимальная длина пароля: {min_length} символов")
        
        if len(password) > 128:
            raise ValidationError("Пароль слишком длинный")
        
        # Проверяем требования к символам
        if require_uppercase and not re.search(r'[A-Z]', password):
            raise ValidationError("Пароль должен содержать заглавные буквы")
        
        if require_lowercase and not re.search(r'[a-z]', password):
            raise ValidationError("Пароль должен содержать строчные буквы")
        
        if require_digits and not re.search(r'\d', password):
            raise ValidationError("Пароль должен содержать цифры")
        
        if require_special and not re.search(r'[@$!%*?&]', password):
            raise ValidationError("Пароль должен содержать специальные символы")
        
        # Проверяем на распространенные пароли
        if check_common and cls._is_common_password(password):
            raise ValidationError("Пароль слишком простой")
        
        # Проверяем на атаки
        cls._check_for_attacks(password)
        
        return password
    
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Валидирует номер телефона.
        
        Args:
            phone: Номер телефона для валидации
        
        Returns:
            Валидированный номер телефона
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(phone, str):
            raise ValidationError("Номер телефона должен быть строкой")
        
        # Удаляем пробелы и дефисы
        phone = re.sub(r'[\s-()]', '', phone)
        
        # Проверяем базовый формат
        if not cls.PATTERNS['phone'].match(phone):
            raise ValidationError("Некорректный формат номера телефона")
        
        # Проверяем длину
        if len(phone) < 7 or len(phone) > 15:
            raise ValidationError("Некорректная длина номера телефона")
        
        return phone
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None) -> str:
        """
        Валидирует URL.
        
        Args:
            url: URL для валидации
            allowed_schemes: Разрешенные схемы (по умолчанию http, https)
        
        Returns:
            Валидированный URL
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(url, str):
            raise ValidationError("URL должен быть строкой")
        
        url = url.strip()
        
        # Проверяем длину
        if len(url) > 2048:
            raise ValidationError("URL слишком длинный")
        
        # Проверяем базовый формат
        if not cls.PATTERNS['url'].match(url):
            raise ValidationError("Некорректный формат URL")
        
        # Проверяем схему
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        scheme = url.split('://')[0].lower()
        if scheme not in allowed_schemes:
            raise ValidationError(f"Недопустимая схема URL: {scheme}")
        
        # Проверяем на подозрительные домены
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if cls._is_suspicious_domain(parsed.netloc):
                raise ValidationError("Подозрительный домен в URL")
        except Exception:
            raise ValidationError("Ошибка парсинга URL")
        
        return url
    
    @classmethod
    def validate_ip_address(cls, ip: str, version: Optional[int] = None) -> str:
        """
        Валидирует IP адрес.
        
        Args:
            ip: IP адрес для валидации
            version: Версия IP (4 или 6, None для любой)
        
        Returns:
            Валидированный IP адрес
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(ip, str):
            raise ValidationError("IP адрес должен быть строкой")
        
        ip = ip.strip()
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Проверяем версию если указана
            if version and ip_obj.version != version:
                raise ValidationError(f"Требуется IPv{version}")
            
            # Проверяем на приватные/зарезервированные адреса
            if ip_obj.is_private:
                logger.info(f"Private IP address used: {ip}")
            
            if ip_obj.is_reserved:
                raise ValidationError("Зарезервированный IP адрес")
            
            if ip_obj.is_loopback:
                logger.info(f"Loopback IP address used: {ip}")
            
            return str(ip_obj)
            
        except ValueError:
            raise ValidationError("Некорректный IP адрес")
    
    @classmethod
    def validate_json(cls, json_str: str, max_depth: int = 10, max_size: int = 1024*1024) -> dict:
        """
        Валидирует JSON строку.
        
        Args:
            json_str: JSON строка для валидации
            max_depth: Максимальная глубина вложенности
            max_size: Максимальный размер в байтах
        
        Returns:
            Распарсенный JSON объект
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if not isinstance(json_str, str):
            raise ValidationError("JSON должен быть строкой")
        
        # Проверяем размер
        if len(json_str.encode('utf-8')) > max_size:
            raise ValidationError("JSON слишком большой")
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Некорректный JSON: {str(e)}")
        
        # Проверяем глубину
        if cls._get_json_depth(data) > max_depth:
            raise ValidationError("JSON слишком глубокий")
        
        return data
    
    @classmethod
    def validate_integer(cls, value: Union[str, int], 
                        min_value: Optional[int] = None,
                        max_value: Optional[int] = None) -> int:
        """
        Валидирует целое число.
        
        Args:
            value: Значение для валидации
            min_value: Минимальное значение
            max_value: Максимальное значение
        
        Returns:
            Валидированное целое число
        
        Raises:
            ValidationError: При ошибке валидации
        """
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                raise ValueError("Не является числом")
        except (ValueError, TypeError):
            raise ValidationError("Значение должно быть целым числом")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"Минимальное значение: {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"Максимальное значение: {max_value}")
        
        return value
    
    @classmethod
    def validate_decimal(cls, value: Union[str, float, Decimal],
                        max_digits: int = 10,
                        decimal_places: int = 2,
                        min_value: Optional[Decimal] = None,
                        max_value: Optional[Decimal] = None) -> Decimal:
        """
        Валидирует десятичное число.
        
        Args:
            value: Значение для валидации
            max_digits: Максимальное количество цифр
            decimal_places: Количество знаков после запятой
            min_value: Минимальное значение
            max_value: Максимальное значение
        
        Returns:
            Валидированное десятичное число
        
        Raises:
            ValidationError: При ошибке валидации
        """
        try:
            if isinstance(value, str):
                value = Decimal(value)
            elif isinstance(value, float):
                value = Decimal(str(value))
            elif not isinstance(value, Decimal):
                raise ValueError("Не является числом")
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError("Значение должно быть десятичным числом")
        
        # Проверяем количество цифр
        sign, digits, exponent = value.as_tuple()
        if len(digits) > max_digits:
            raise ValidationError(f"Максимальное количество цифр: {max_digits}")
        
        # Проверяем знаки после запятой
        if exponent < -decimal_places:
            raise ValidationError(f"Максимальное количество знаков после запятой: {decimal_places}")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"Минимальное значение: {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"Максимальное значение: {max_value}")
        
        return value
    
    @classmethod
    def validate_date(cls, value: Union[str, date, datetime], 
                     min_date: Optional[date] = None,
                     max_date: Optional[date] = None,
                     date_format: str = '%Y-%m-%d') -> date:
        """
        Валидирует дату.
        
        Args:
            value: Значение для валидации
            min_date: Минимальная дата
            max_date: Максимальная дата
            date_format: Формат даты для строк
        
        Returns:
            Валидированная дата
        
        Raises:
            ValidationError: При ошибке валидации
        """
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, date_format).date()
            except ValueError:
                raise ValidationError(f"Некорректный формат даты. Ожидается: {date_format}")
        elif isinstance(value, datetime):
            value = value.date()
        elif not isinstance(value, date):
            raise ValidationError("Значение должно быть датой")
        
        if min_date and value < min_date:
            raise ValidationError(f"Минимальная дата: {min_date}")
        
        if max_date and value > max_date:
            raise ValidationError(f"Максимальная дата: {max_date}")
        
        return value
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """
        Санитизирует строку от опасного контента.
        
        Args:
            value: Строка для санитизации
        
        Returns:
            Санитизированная строка
        """
        if not isinstance(value, str):
            return value
        
        # Удаляем null байты
        value = value.replace('\x00', '')
        
        # Удаляем управляющие символы
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Экранируем HTML
        value = escape(value)
        
        # Удаляем потенциально опасные последовательности
        dangerous_sequences = [
            'javascript:', 'vbscript:', 'data:', 'about:',
            '<script', '</script>', '<iframe', '</iframe>',
            '<object', '</object>', '<embed', '</embed>',
            'onload=', 'onerror=', 'onclick=', 'onmouseover='
        ]
        
        value_lower = value.lower()
        for seq in dangerous_sequences:
            if seq in value_lower:
                value = value.replace(seq, '')
                value = value.replace(seq.upper(), '')
                value = value.replace(seq.capitalize(), '')
        
        return value.strip()
    
    @classmethod
    def _check_for_attacks(cls, value: str) -> None:
        """
        Проверяет строку на наличие паттернов атак.
        
        Args:
            value: Строка для проверки
        
        Raises:
            ValidationError: При обнаружении подозрительных паттернов
        """
        for attack_type, patterns in cls.ATTACK_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(value):
                    logger.warning(f"Potential {attack_type} attack detected: {value[:100]}")
                    raise ValidationError(f"Обнаружены потенциально опасные данные")
    
    @classmethod
    def _is_suspicious_domain(cls, domain: str) -> bool:
        """
        Проверяет домен на подозрительность.
        
        Args:
            domain: Домен для проверки
        
        Returns:
            True если домен подозрительный
        """
        # Список подозрительных доменов (можно расширить)
        suspicious_domains = [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org'
        ]
        
        # Проверяем на точное совпадение
        if domain.lower() in suspicious_domains:
            return True
        
        # Проверяем на подозрительные паттерны
        suspicious_patterns = [
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP адрес
            r'[a-z0-9]{20,}\.',  # Очень длинные случайные строки
            r'\.(tk|ml|ga|cf)$',  # Подозрительные TLD
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain.lower()):
                return True
        
        return False
    
    @classmethod
    def _is_common_password(cls, password: str) -> bool:
        """
        Проверяет, является ли пароль распространенным.
        
        Args:
            password: Пароль для проверки
        
        Returns:
            True если пароль распространенный
        """
        # Список распространенных паролей
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            'dragon', 'master', 'shadow', 'superman', 'michael',
            'football', 'baseball', 'liverpool', 'jordan', 'princess'
        ]
        
        password_lower = password.lower()
        
        # Проверяем точное совпадение
        if password_lower in common_passwords:
            return True
        
        # Проверяем простые вариации
        for common in common_passwords:
            if password_lower.startswith(common) or password_lower.endswith(common):
                return True
        
        # Проверяем последовательности
        sequences = ['123456', 'abcdef', 'qwerty', '987654', 'fedcba']
        for seq in sequences:
            if seq in password_lower or seq[::-1] in password_lower:
                return True
        
        return False
    
    @classmethod
    def _get_json_depth(cls, obj: Any, depth: int = 0) -> int:
        """
        Вычисляет глубину JSON объекта.
        
        Args:
            obj: JSON объект
            depth: Текущая глубина
        
        Returns:
            Максимальная глубина
        """
        if isinstance(obj, dict):
            return max([cls._get_json_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([cls._get_json_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth


class DataIntegrityValidator:
    """
    Валидатор для проверки целостности данных.
    """
    
    @staticmethod
    def validate_checksum(data: bytes, expected_checksum: str, algorithm: str = 'sha256') -> bool:
        """
        Проверяет контрольную сумму данных.
        
        Args:
            data: Данные для проверки
            expected_checksum: Ожидаемая контрольная сумма
            algorithm: Алгоритм хеширования
        
        Returns:
            True если контрольная сумма совпадает
        """
        try:
            hasher = hashlib.new(algorithm)
            hasher.update(data)
            actual_checksum = hasher.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
        except Exception as e:
            logger.error(f"Checksum validation error: {str(e)}")
            return False
    
    @staticmethod
    def validate_data_consistency(data: Dict[str, Any], rules: Dict[str, Callable]) -> List[str]:
        """
        Проверяет консистентность данных согласно правилам.
        
        Args:
            data: Данные для проверки
            rules: Правила валидации {rule_name: validation_function}
        
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        for rule_name, rule_func in rules.items():
            try:
                if not rule_func(data):
                    errors.append(f"Нарушено правило: {rule_name}")
            except Exception as e:
                errors.append(f"Ошибка проверки правила {rule_name}: {str(e)}")
        
        return errors