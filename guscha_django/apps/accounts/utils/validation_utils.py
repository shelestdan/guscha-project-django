from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, Dict, Any, List, Union, Tuple
import re
import phonenumbers
from phonenumbers import NumberParseException
import logging
from datetime import datetime, date
import json
from urllib.parse import urlparse
import ipaddress

logger = logging.getLogger(__name__)


class ValidationUtils:
    """Утилиты для валидации данных"""
    
    # Регулярные выражения
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
    TELEGRAM_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
    PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # Константы
    MIN_AGE = 13
    MAX_AGE = 120
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """Валидация email адреса"""
        if not email:
            return {
                'is_valid': False,
                'error': 'Email не может быть пустым'
            }
        
        try:
            django_validate_email(email)
            
            # Дополнительные проверки
            if len(email) > 254:
                return {
                    'is_valid': False,
                    'error': 'Email слишком длинный'
                }
            
            # Проверка на запрещенные домены
            domain = email.split('@')[1].lower()
            forbidden_domains = ['tempmail.org', '10minutemail.com', 'guerrillamail.com']
            if domain in forbidden_domains:
                return {
                    'is_valid': False,
                    'error': 'Использование временных email адресов запрещено'
                }
            
            return {
                'is_valid': True,
                'normalized_email': email.lower().strip()
            }
            
        except ValidationError as e:
            return {
                'is_valid': False,
                'error': 'Некорректный формат email адреса'
            }
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """Валидация имени пользователя"""
        if not username:
            return {
                'is_valid': False,
                'error': 'Имя пользователя не может быть пустым'
            }
        
        if len(username) < 3:
            return {
                'is_valid': False,
                'error': 'Имя пользователя должно содержать минимум 3 символа'
            }
        
        if len(username) > 30:
            return {
                'is_valid': False,
                'error': 'Имя пользователя не должно превышать 30 символов'
            }
        
        if not ValidationUtils.USERNAME_PATTERN.match(username):
            return {
                'is_valid': False,
                'error': 'Имя пользователя может содержать только буквы, цифры, точки, дефисы и подчеркивания'
            }
        
        # Проверка на запрещенные имена
        forbidden_usernames = ['admin', 'root', 'administrator', 'moderator', 'support', 'help']
        if username.lower() in forbidden_usernames:
            return {
                'is_valid': False,
                'error': 'Данное имя пользователя зарезервировано'
            }
        
        return {
            'is_valid': True,
            'normalized_username': username.lower().strip()
        }
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Валидация имени/фамилии"""
        if not name:
            return False
        
        # Проверка длины
        if len(name.strip()) < 2 or len(name.strip()) > 50:
            return False
        
        # Проверка на допустимые символы (буквы, пробелы, дефисы, апострофы)
        name_pattern = re.compile(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$")
        return bool(name_pattern.match(name.strip()))
    
    @staticmethod
    def password_contains_personal_info(password: str, email: str = '', first_name: str = '', last_name: str = '') -> bool:
        """Проверка, содержит ли пароль личную информацию"""
        if not password:
            return False
        
        password_lower = password.lower()
        
        # Проверка email
        if email:
            email_parts = email.lower().split('@')
            if email_parts[0] and len(email_parts[0]) >= 3 and email_parts[0] in password_lower:
                return True
        
        # Проверка имени
        if first_name and len(first_name) >= 3 and first_name.lower() in password_lower:
            return True
        
        # Проверка фамилии
        if last_name and len(last_name) >= 3 and last_name.lower() in password_lower:
            return True
        
        return False
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = 'RU') -> Dict[str, Any]:
        """Валидация номера телефона"""
        if not phone:
            return {
                'is_valid': False,
                'error': 'Номер телефона не может быть пустым'
            }
        
        try:
            # Парсим номер телефона
            parsed_number = phonenumbers.parse(phone, country_code)
            
            # Проверяем валидность
            if not phonenumbers.is_valid_number(parsed_number):
                return {
                    'is_valid': False,
                    'error': 'Некорректный номер телефона'
                }
            
            # Форматируем номер
            formatted_number = phonenumbers.format_number(
                parsed_number, 
                phonenumbers.PhoneNumberFormat.E164
            )
            
            return {
                'is_valid': True,
                'formatted_number': formatted_number,
                'country_code': parsed_number.country_code,
                'national_number': parsed_number.national_number
            }
            
        except NumberParseException as e:
            error_messages = {
                NumberParseException.INVALID_COUNTRY_CODE: 'Некорректный код страны',
                NumberParseException.NOT_A_NUMBER: 'Не является номером телефона',
                NumberParseException.TOO_SHORT_NSN: 'Номер телефона слишком короткий',
                NumberParseException.TOO_LONG: 'Номер телефона слишком длинный'
            }
            
            return {
                'is_valid': False,
                'error': error_messages.get(e.error_type, 'Некорректный номер телефона')
            }
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Нормализация номера телефона для сравнения"""
        if not phone:
            return ""
        
        # Удаляем все символы кроме цифр и знака +
        normalized = re.sub(r'[^\d+]', '', phone)
        
        # Если номер начинается с 8, заменяем на +7 (для российских номеров)
        if normalized.startswith('8') and len(normalized) == 11:
            normalized = '+7' + normalized[1:]
        
        # Если номер начинается с 7 без +, добавляем +
        elif normalized.startswith('7') and len(normalized) == 11:
            normalized = '+' + normalized
            
        # Если номер не содержит код страны, пытаемся определить его через phonenumbers
        if not normalized.startswith('+'):
            try:
                parsed = phonenumbers.parse(normalized, 'RU')
                normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            except Exception as e:
                # Если не удалось распарсить, возвращаем как есть
                logger.debug(f"Не удалось нормализовать номер телефона {phone}: {e}")
                
        return normalized
    

    @staticmethod
    def validate_telegram_username(username: str) -> Dict[str, Any]:
        """Валидация Telegram имени пользователя"""
        if not username:
            return {
                'is_valid': False,
                'error': 'Telegram имя пользователя не может быть пустым'
            }
        
        # Убираем @ если есть
        clean_username = username.lstrip('@')
        
        if not ValidationUtils.TELEGRAM_USERNAME_PATTERN.match(clean_username):
            return {
                'is_valid': False,
                'error': 'Telegram имя пользователя должно содержать 5-32 символа (буквы, цифры, подчеркивания)'
            }
        
        return {
            'is_valid': True,
            'normalized_username': clean_username
        }
    
    @staticmethod
    def validate_telegram_chat_id(chat_id: Union[str, int]) -> Dict[str, Any]:
        """Валидация Telegram chat ID"""
        if not chat_id:
            return {
                'is_valid': False,
                'error': 'Chat ID не может быть пустым'
            }
        
        try:
            chat_id_int = int(chat_id)
            
            # Telegram chat ID должен быть положительным числом
            if chat_id_int <= 0:
                return {
                    'is_valid': False,
                    'error': 'Chat ID должен быть положительным числом'
                }
            
            return {
                'is_valid': True,
                'chat_id': chat_id_int
            }
            
        except (ValueError, TypeError):
            return {
                'is_valid': False,
                'error': 'Chat ID должен быть числом'
            }
    
    @staticmethod
    def validate_url(url: str) -> Dict[str, Any]:
        """Валидация URL"""
        if not url:
            return {
                'is_valid': False,
                'error': 'URL не может быть пустым'
            }
        
        if not ValidationUtils.URL_PATTERN.match(url):
            return {
                'is_valid': False,
                'error': 'Некорректный формат URL'
            }
        
        try:
            parsed = urlparse(url)
            
            # Проверяем схему
            if parsed.scheme not in ['http', 'https']:
                return {
                    'is_valid': False,
                    'error': 'URL должен использовать HTTP или HTTPS протокол'
                }
            
            # Проверяем наличие домена
            if not parsed.netloc:
                return {
                    'is_valid': False,
                    'error': 'URL должен содержать домен'
                }
            
            return {
                'is_valid': True,
                'parsed_url': {
                    'scheme': parsed.scheme,
                    'netloc': parsed.netloc,
                    'path': parsed.path,
                    'params': parsed.params,
                    'query': parsed.query,
                    'fragment': parsed.fragment
                }
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Ошибка при разборе URL: {str(e)}'
            }
    
    @staticmethod
    def validate_date(date_value: Union[str, date, datetime], min_date: date = None, max_date: date = None) -> Dict[str, Any]:
        """Валидация даты"""
        if not date_value:
            return {
                'is_valid': False,
                'error': 'Дата не может быть пустой'
            }
        
        try:
            # Преобразуем в объект date
            if isinstance(date_value, str):
                # Пробуем разные форматы
                formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
                parsed_date = None
                
                for fmt in formats:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    return {
                        'is_valid': False,
                        'error': 'Некорректный формат даты'
                    }
                    
            elif isinstance(date_value, datetime):
                parsed_date = date_value.date()
            elif isinstance(date_value, date):
                parsed_date = date_value
            else:
                return {
                    'is_valid': False,
                    'error': 'Неподдерживаемый тип даты'
                }
            
            # Проверяем диапазон
            if min_date and parsed_date < min_date:
                return {
                    'is_valid': False,
                    'error': f'Дата не может быть раньше {min_date}'
                }
            
            if max_date and parsed_date > max_date:
                return {
                    'is_valid': False,
                    'error': f'Дата не может быть позже {max_date}'
                }
            
            return {
                'is_valid': True,
                'parsed_date': parsed_date
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Ошибка при обработке даты: {str(e)}'
            }
    
    @staticmethod
    def validate_age(birth_date: Union[str, date, datetime]) -> Dict[str, Any]:
        """Валидация возраста"""
        date_result = ValidationUtils.validate_date(birth_date)
        if not date_result['is_valid']:
            return date_result
        
        birth_date_obj = date_result['parsed_date']
        today = timezone.now().date()
        
        # Вычисляем возраст
        age = today.year - birth_date_obj.year
        if today.month < birth_date_obj.month or (today.month == birth_date_obj.month and today.day < birth_date_obj.day):
            age -= 1
        
        if age < ValidationUtils.MIN_AGE:
            return {
                'is_valid': False,
                'error': f'Минимальный возраст: {ValidationUtils.MIN_AGE} лет'
            }
        
        if age > ValidationUtils.MAX_AGE:
            return {
                'is_valid': False,
                'error': f'Максимальный возраст: {ValidationUtils.MAX_AGE} лет'
            }
        
        return {
            'is_valid': True,
            'age': age,
            'birth_date': birth_date_obj
        }
    
    @staticmethod
    def validate_json(json_string: str) -> Dict[str, Any]:
        """Валидация JSON строки"""
        if not json_string:
            return {
                'is_valid': False,
                'error': 'JSON строка не может быть пустой'
            }
        
        try:
            parsed_json = json.loads(json_string)
            return {
                'is_valid': True,
                'parsed_json': parsed_json
            }
        except json.JSONDecodeError as e:
            return {
                'is_valid': False,
                'error': f'Некорректный JSON: {str(e)}'
            }
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> Dict[str, Any]:
        """Валидация IP адреса"""
        if not ip_address:
            return {
                'is_valid': False,
                'error': 'IP адрес не может быть пустым'
            }
        
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            
            return {
                'is_valid': True,
                'ip_address': str(ip_obj),
                'version': ip_obj.version,
                'is_private': ip_obj.is_private,
                'is_global': ip_obj.is_global,
                'is_loopback': ip_obj.is_loopback
            }
            
        except ValueError as e:
            return {
                'is_valid': False,
                'error': 'Некорректный IP адрес'
            }
    
    @staticmethod
    def validate_numeric_range(value: Union[str, int, float], min_value: float = None, max_value: float = None) -> Dict[str, Any]:
        """Валидация числового диапазона"""
        if value is None or value == '':
            return {
                'is_valid': False,
                'error': 'Значение не может быть пустым'
            }
        
        try:
            numeric_value = float(value)
            
            if min_value is not None and numeric_value < min_value:
                return {
                    'is_valid': False,
                    'error': f'Значение должно быть не менее {min_value}'
                }
            
            if max_value is not None and numeric_value > max_value:
                return {
                    'is_valid': False,
                    'error': f'Значение должно быть не более {max_value}'
                }
            
            return {
                'is_valid': True,
                'numeric_value': numeric_value
            }
            
        except (ValueError, TypeError):
            return {
                'is_valid': False,
                'error': 'Значение должно быть числом'
            }
    
    @staticmethod
    def validate_string_length(text: str, min_length: int = None, max_length: int = None) -> Dict[str, Any]:
        """Валидация длины строки"""
        if text is None:
            text = ''
        
        length = len(text)
        
        if min_length is not None and length < min_length:
            return {
                'is_valid': False,
                'error': f'Минимальная длина: {min_length} символов'
            }
        
        if max_length is not None and length > max_length:
            return {
                'is_valid': False,
                'error': f'Максимальная длина: {max_length} символов'
            }
        
        return {
            'is_valid': True,
            'length': length
        }
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any]) -> Dict[str, Any]:
        """Валидация выбора из списка"""
        if value not in choices:
            return {
                'is_valid': False,
                'error': f'Значение должно быть одним из: {", ".join(map(str, choices))}'
            }
        
        return {
            'is_valid': True,
            'value': value
        }
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> Dict[str, Any]:
        """Валидация расширения файла"""
        if not filename:
            return {
                'is_valid': False,
                'error': 'Имя файла не может быть пустым'
            }
        
        if '.' not in filename:
            return {
                'is_valid': False,
                'error': 'Файл должен иметь расширение'
            }
        
        extension = '.' + filename.split('.')[-1].lower()
        
        if extension not in [ext.lower() for ext in allowed_extensions]:
            return {
                'is_valid': False,
                'error': f'Разрешенные расширения: {", ".join(allowed_extensions)}'
            }
        
        return {
            'is_valid': True,
            'extension': extension
        }
    
    @staticmethod
    def validate_multiple_fields(data: Dict[str, Any], validation_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация нескольких полей"""
        errors = {}
        validated_data = {}
        
        for field_name, rules in validation_rules.items():
            field_value = data.get(field_name)
            field_errors = []
            
            # Проверка обязательности
            if rules.get('required', False) and not field_value:
                field_errors.append(f'Поле {field_name} обязательно для заполнения')
                continue
            
            # Если поле не обязательное и пустое, пропускаем валидацию
            if not field_value and not rules.get('required', False):
                validated_data[field_name] = field_value
                continue
            
            # Валидация типа
            field_type = rules.get('type')
            if field_type == 'email':
                result = ValidationUtils.validate_email(field_value)
            elif field_type == 'username':
                result = ValidationUtils.validate_username(field_value)
            elif field_type == 'phone':
                result = ValidationUtils.validate_phone_number(field_value)
            elif field_type == 'url':
                result = ValidationUtils.validate_url(field_value)
            elif field_type == 'date':
                result = ValidationUtils.validate_date(field_value)
            elif field_type == 'numeric':
                result = ValidationUtils.validate_numeric_range(
                    field_value, 
                    rules.get('min_value'), 
                    rules.get('max_value')
                )
            elif field_type == 'string':
                result = ValidationUtils.validate_string_length(
                    field_value, 
                    rules.get('min_length'), 
                    rules.get('max_length')
                )
            elif field_type == 'choice':
                result = ValidationUtils.validate_choice(field_value, rules.get('choices', []))
            else:
                result = {'is_valid': True}
            
            if not result['is_valid']:
                field_errors.append(result['error'])
            else:
                # Используем нормализованное значение если есть
                if 'normalized_email' in result:
                    validated_data[field_name] = result['normalized_email']
                elif 'normalized_username' in result:
                    validated_data[field_name] = result['normalized_username']
                elif 'formatted_number' in result:
                    validated_data[field_name] = result['formatted_number']
                elif 'parsed_date' in result:
                    validated_data[field_name] = result['parsed_date']
                elif 'numeric_value' in result:
                    validated_data[field_name] = result['numeric_value']
                else:
                    validated_data[field_name] = field_value
            
            if field_errors:
                errors[field_name] = field_errors
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'validated_data': validated_data
        }
    
    @staticmethod
    def sanitize_html(html_string: str) -> str:
        """Санитизация HTML (базовая)"""
        if not html_string:
            return ''
        
        # Удаляем потенциально опасные теги
        dangerous_tags = ['<script', '</script>', '<iframe', '</iframe>', '<object', '</object>', 
                         '<embed', '</embed>', '<form', '</form>', '<input', '<button']
        
        sanitized = html_string
        for tag in dangerous_tags:
            sanitized = re.sub(re.escape(tag), '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста"""
        if not text:
            return ''
        
        # Удаляем лишние пробелы
        normalized = ' '.join(text.split())
        
        # Приводим к нижнему регистру
        normalized = normalized.lower()
        
        # Удаляем специальные символы (оставляем только буквы, цифры и пробелы)
        normalized = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', normalized)
        
        return normalized.strip()
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Проверка силы пароля"""
        if not password:
            return {
                'is_valid': False,
                'score': 0,
                'errors': ['Пароль не может быть пустым']
            }
        
        errors = []
        score = 0
        
        # Константы
        PASSWORD_MIN_LENGTH = 8
        PASSWORD_MAX_LENGTH = 128
        
        # Регулярные выражения для проверки пароля
        PASSWORD_PATTERNS = {
            'lowercase': re.compile(r'[a-z]'),
            'uppercase': re.compile(r'[A-Z]'),
            'digit': re.compile(r'\d'),
            'special': re.compile(r'[!@#$%^&*(),.?":{}|<>]'),
            'no_spaces': re.compile(r'^\S*$')
        }
        
        # Проверка длины
        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(f'Пароль должен содержать минимум {PASSWORD_MIN_LENGTH} символов')
        elif len(password) >= PASSWORD_MIN_LENGTH:
            score += 1
        
        if len(password) > PASSWORD_MAX_LENGTH:
            errors.append(f'Пароль не должен превышать {PASSWORD_MAX_LENGTH} символов')
        
        # Проверка наличия строчных букв
        if PASSWORD_PATTERNS['lowercase'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать строчные буквы')
        
        # Проверка наличия заглавных букв
        if PASSWORD_PATTERNS['uppercase'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать заглавные буквы')
        
        # Проверка наличия цифр
        if PASSWORD_PATTERNS['digit'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать цифры')
        
        # Проверка наличия специальных символов
        if PASSWORD_PATTERNS['special'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать специальные символы')
        
        # Проверка отсутствия пробелов
        if not PASSWORD_PATTERNS['no_spaces'].search(password):
            errors.append('Пароль не должен содержать пробелы')
            score -= 1
        
        # Проверка на повторяющиеся символы
        if len(set(password)) < len(password) * 0.7:
            errors.append('Пароль содержит слишком много повторяющихся символов')
            score -= 1
        
        # Проверка на последовательности
        if ValidationUtils._has_sequential_chars(password):
            errors.append('Пароль не должен содержать последовательности символов')
            score -= 1
        
        # Проверка на общие пароли
        if ValidationUtils._is_common_password(password):
            errors.append('Пароль слишком простой')
            score -= 2
        
        # Нормализация счета
        score = max(0, min(5, score))
        
        return {
            'is_valid': len(errors) == 0 and score >= 3,
            'score': score,
            'errors': errors,
            'strength': ValidationUtils._get_password_strength_label(score)
        }
    
    @staticmethod
    def _has_sequential_chars(password: str) -> bool:
        """Проверка на последовательности символов"""
        # Смягченная проверка - только длинные последовательности (4+ символа)
        sequences = ['1234', '2345', '3456', '4567', '5678', '6789', '7890',
                    'abcd', 'bcde', 'cdef', 'defg', 'efgh', 'fghi', 'ghij',
                    'qwer', 'wert', 'erty', 'rtyu', 'tyui', 'yuio', 'uiop']
        
        password_lower = password.lower()
        for seq in sequences:
            if seq in password_lower or seq[::-1] in password_lower:
                return True
        return False
    
    @staticmethod
    def _is_common_password(password: str) -> bool:
        """Проверка на общие пароли"""
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            'пароль', '123456', 'qwerty', 'admin123'
        ]
        
        return password.lower() in common_passwords
    
    @staticmethod
    def _get_password_strength_label(score: int) -> str:
        """Получение метки силы пароля"""
        if score <= 1:
            return 'Очень слабый'
        elif score == 2:
            return 'Слабый'
        elif score == 3:
            return 'Средний'
        elif score == 4:
            return 'Сильный'
        else:
            return 'Очень сильный'
    
    @staticmethod
    def get_validation_summary(validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Получение сводки по результатам валидации"""
        total_validations = len(validation_results)
        successful_validations = sum(1 for result in validation_results if result.get('is_valid', False))
        failed_validations = total_validations - successful_validations
        
        all_errors = []
        for result in validation_results:
            if not result.get('is_valid', False):
                error = result.get('error', 'Неизвестная ошибка')
                if isinstance(error, list):
                    all_errors.extend(error)
                else:
                    all_errors.append(error)
        
        return {
            'total_validations': total_validations,
            'successful_validations': successful_validations,
            'failed_validations': failed_validations,
            'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0,
            'all_errors': all_errors,
            'is_all_valid': failed_validations == 0
        }