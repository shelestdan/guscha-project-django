from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from typing import Optional, Dict, Any, List, Tuple
import hashlib
import hmac
import secrets
import string
import re
import ipaddress
import logging
from datetime import datetime, timedelta
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecurityUtils:
    """Утилиты для обеспечения безопасности"""
    
    # Константы
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    
    # Регулярные выражения для проверки пароля
    PASSWORD_PATTERNS = {
        'lowercase': re.compile(r'[a-z]'),
        'uppercase': re.compile(r'[A-Z]'),
        'digit': re.compile(r'\d'),
        # Расширяем список допустимых специальных символов, добавив дефис (-), подчёркивание (_), плюс (+)
        'special': re.compile(r'[!@#$%^\u0026*()_\-+.,?":{}|\u003c\u003e]'),
        'no_spaces': re.compile(r'^\S*$')
    }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        try:
            return make_password(password)
        except Exception as e:
            logger.error(f'Failed to hash password: {str(e)}')
            raise
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            return check_password(password, hashed_password)
        except Exception as e:
            logger.error(f'Failed to verify password: {str(e)}')
            return False
    
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
        
        # Проверка длины
        if len(password) < SecurityUtils.PASSWORD_MIN_LENGTH:
            errors.append(f'Пароль должен содержать минимум {SecurityUtils.PASSWORD_MIN_LENGTH} символов')
        elif len(password) >= SecurityUtils.PASSWORD_MIN_LENGTH:
            score += 1
        
        if len(password) > SecurityUtils.PASSWORD_MAX_LENGTH:
            errors.append(f'Пароль не должен превышать {SecurityUtils.PASSWORD_MAX_LENGTH} символов')
        
        # Проверка наличия строчных букв
        if SecurityUtils.PASSWORD_PATTERNS['lowercase'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать строчные буквы')
        
        # Проверка наличия заглавных букв
        if SecurityUtils.PASSWORD_PATTERNS['uppercase'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать заглавные буквы')
        
        # Проверка наличия цифр
        if SecurityUtils.PASSWORD_PATTERNS['digit'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать цифры')
        
        # Проверка наличия специальных символов
        if SecurityUtils.PASSWORD_PATTERNS['special'].search(password):
            score += 1
        else:
            errors.append('Пароль должен содержать специальные символы')
        
        # Проверка отсутствия пробелов
        if not SecurityUtils.PASSWORD_PATTERNS['no_spaces'].search(password):
            errors.append('Пароль не должен содержать пробелы')
            score -= 1
        
        # Проверка на повторяющиеся символы
        if len(set(password)) < len(password) * 0.7:
            errors.append('Пароль содержит слишком много повторяющихся символов')
            score -= 1
        
        # Проверка на последовательности
        if SecurityUtils._has_sequential_chars(password):
            errors.append('Пароль не должен содержать последовательности символов')
            score -= 1
        
        # Проверка на общие пароли
        if SecurityUtils._is_common_password(password):
            errors.append('Пароль слишком простой')
            score -= 2
        
        # Нормализация счета
        score = max(0, min(5, score))
        
        return {
            'is_valid': len(errors) == 0 and score >= 3,
            'score': score,
            'errors': errors,
            'strength': SecurityUtils._get_password_strength_label(score)
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
    def is_ip_allowed(ip: str) -> bool:
        """Проверка, разрешен ли IP-адрес"""
        try:
            # Пример проверки IP (определите свои правила)
            allowed_ips = getattr(settings, 'ALLOWED_IPS', [])
            return ip in allowed_ips
        except Exception as e:
            logger.error(f'Ошибка при проверке IP: {str(e)}')
            return False

    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Генерация безопасного пароля"""
        if length < SecurityUtils.PASSWORD_MIN_LENGTH:
            length = SecurityUtils.PASSWORD_MIN_LENGTH
        
        # Обеспечиваем наличие всех типов символов
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()'
        
        # Гарантируем минимум по одному символу каждого типа
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Заполняем оставшуюся длину
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Перемешиваем
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def check_rate_limit(identifier: str, max_attempts: int = None, window_minutes: int = None) -> Dict[str, Any]:
        """Проверка ограничения скорости запросов"""
        if max_attempts is None:
            max_attempts = SecurityUtils.MAX_LOGIN_ATTEMPTS
        if window_minutes is None:
            window_minutes = SecurityUtils.LOCKOUT_DURATION_MINUTES
        
        cache_key = f'rate_limit:{identifier}'
        
        try:
            # Получаем текущие данные из кеша
            rate_data = cache.get(cache_key, {'attempts': 0, 'first_attempt': None, 'locked_until': None})
            
            now = timezone.now()
            
            # Проверяем, заблокирован ли пользователь
            if rate_data.get('locked_until') and now < rate_data['locked_until']:
                remaining_time = rate_data['locked_until'] - now
                return {
                    'allowed': False,
                    'attempts_remaining': 0,
                    'locked_until': rate_data['locked_until'],
                    'remaining_time_seconds': int(remaining_time.total_seconds())
                }
            
            # Сбрасываем блокировку, если время истекло
            if rate_data.get('locked_until') and now >= rate_data['locked_until']:
                rate_data = {'attempts': 0, 'first_attempt': None, 'locked_until': None}
            
            # Проверяем окно времени
            if rate_data.get('first_attempt'):
                time_diff = now - rate_data['first_attempt']
                if time_diff.total_seconds() > window_minutes * 60:
                    # Окно истекло, сбрасываем счетчик
                    rate_data = {'attempts': 0, 'first_attempt': None, 'locked_until': None}
            
            attempts_remaining = max_attempts - rate_data['attempts']
            
            return {
                'allowed': attempts_remaining > 0,
                'attempts_remaining': attempts_remaining,
                'locked_until': None,
                'remaining_time_seconds': 0
            }
            
        except Exception as e:
            logger.error(f'Failed to check rate limit for {identifier}: {str(e)}')
            # В случае ошибки разрешаем запрос
            return {
                'allowed': True,
                'attempts_remaining': max_attempts,
                'locked_until': None,
                'remaining_time_seconds': 0
            }
    
    @staticmethod
    def record_failed_attempt(identifier: str, max_attempts: int = None, window_minutes: int = None) -> Dict[str, Any]:
        """Запись неудачной попытки"""
        if max_attempts is None:
            max_attempts = SecurityUtils.MAX_LOGIN_ATTEMPTS
        if window_minutes is None:
            window_minutes = SecurityUtils.LOCKOUT_DURATION_MINUTES
        
        cache_key = f'rate_limit:{identifier}'
        
        try:
            # Получаем текущие данные
            rate_data = cache.get(cache_key, {'attempts': 0, 'first_attempt': None, 'locked_until': None})
            
            now = timezone.now()
            
            # Устанавливаем время первой попытки
            if not rate_data.get('first_attempt'):
                rate_data['first_attempt'] = now
            
            # Увеличиваем счетчик
            rate_data['attempts'] += 1
            
            # Проверяем, нужно ли заблокировать
            if rate_data['attempts'] >= max_attempts:
                rate_data['locked_until'] = now + timedelta(minutes=window_minutes)
                logger.warning(f'Rate limit exceeded for {identifier}, locked until {rate_data["locked_until"]}')
            
            # Сохраняем в кеш
            cache.set(cache_key, rate_data, timeout=window_minutes * 60 * 2)  # Удваиваем время для надежности
            
            attempts_remaining = max_attempts - rate_data['attempts']
            
            return {
                'attempts_remaining': max(0, attempts_remaining),
                'locked_until': rate_data.get('locked_until'),
                'is_locked': rate_data['attempts'] >= max_attempts
            }
            
        except Exception as e:
            logger.error(f'Failed to record failed attempt for {identifier}: {str(e)}')
            return {
                'attempts_remaining': 0,
                'locked_until': None,
                'is_locked': False
            }
    
    @staticmethod
    def reset_rate_limit(identifier: str) -> bool:
        """Сброс ограничения скорости"""
        cache_key = f'rate_limit:{identifier}'
        
        try:
            cache.delete(cache_key)
            logger.info(f'Rate limit reset for {identifier}')
            return True
        except Exception as e:
            logger.error(f'Failed to reset rate limit for {identifier}: {str(e)}')
            return False
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> bool:
        """Проверка корректности IP адреса"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_ip_whitelisted(ip_address: str) -> bool:
        """Проверка, находится ли IP в белом списке"""
        whitelist = getattr(settings, 'IP_WHITELIST', [])
        
        if not whitelist:
            return True  # Если белый список пуст, разрешаем все
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for allowed_ip in whitelist:
                if '/' in allowed_ip:  # Подсеть
                    if ip in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:  # Отдельный IP
                    if ip == ipaddress.ip_address(allowed_ip):
                        return True
            return False
        except ValueError:
            return False
    
    @staticmethod
    def is_ip_blacklisted(ip_address: str) -> bool:
        """Проверка, находится ли IP в черном списке"""
        blacklist = getattr(settings, 'IP_BLACKLIST', [])
        
        if not blacklist:
            return False  # Если черный список пуст, не блокируем
        
        try:
            ip = ipaddress.ip_address(ip_address)
            for blocked_ip in blacklist:
                if '/' in blocked_ip:  # Подсеть
                    if ip in ipaddress.ip_network(blocked_ip, strict=False):
                        return True
                else:  # Отдельный IP
                    if ip == ipaddress.ip_address(blocked_ip):
                        return True
            return False
        except ValueError:
            return True  # В случае ошибки блокируем
    
    @staticmethod
    def create_csrf_token() -> str:
        """Создание CSRF токена"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, expected_token: str) -> bool:
        """Проверка CSRF токена"""
        if not token or not expected_token:
            return False
        
        return hmac.compare_digest(token, expected_token)
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Санитизация пользовательского ввода"""
        if not input_string:
            return ''
        
        # Обрезаем до максимальной длины
        sanitized = input_string[:max_length]
        
        # Удаляем потенциально опасные символы
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Удаляем лишние пробелы
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def encrypt_data(data: str, key: str = None) -> str:
        """Шифрование данных"""
        try:
            if key is None:
                key = getattr(settings, 'ENCRYPTION_KEY', settings.SECRET_KEY)
            
            # Создаем ключ для Fernet
            key_bytes = key.encode()[:32].ljust(32, b'0')
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'salt_',
                iterations=100000,
            )
            fernet_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            
            fernet = Fernet(fernet_key)
            encrypted_data = fernet.encrypt(data.encode())
            
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f'Failed to encrypt data: {str(e)}')
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str = None) -> str:
        """Расшифровка данных"""
        try:
            if key is None:
                key = getattr(settings, 'ENCRYPTION_KEY', settings.SECRET_KEY)
            
            # Создаем ключ для Fernet
            key_bytes = key.encode()[:32].ljust(32, b'0')
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'salt_',
                iterations=100000,
            )
            fernet_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            
            fernet = Fernet(fernet_key)
            
            # Декодируем и расшифровываем
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f'Failed to decrypt data: {str(e)}')
            raise
    
    @staticmethod
    def create_signature(data: str, secret: str = None) -> str:
        """Создание подписи для данных"""
        if secret is None:
            secret = settings.SECRET_KEY
        
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_signature(data: str, signature: str, secret: str = None) -> bool:
        """Проверка подписи данных"""
        if secret is None:
            secret = settings.SECRET_KEY
        
        expected_signature = SecurityUtils.create_signature(data, secret)
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
        """Маскировка чувствительных данных"""
        if not data or len(data) <= visible_chars:
            return mask_char * len(data) if data else ''
        
        visible_start = visible_chars // 2
        visible_end = visible_chars - visible_start
        
        masked_middle = mask_char * (len(data) - visible_chars)
        
        return data[:visible_start] + masked_middle + data[-visible_end:] if visible_end > 0 else data[:visible_start] + masked_middle
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any], user_id: int = None, ip_address: str = None) -> None:
        """Логирование событий безопасности"""
        try:
            log_data = {
                'event_type': event_type,
                'timestamp': timezone.now().isoformat(),
                'user_id': user_id,
                'ip_address': ip_address,
                'details': details
            }
            
            logger.warning(f'Security event: {json.dumps(log_data)}')
            
            # Здесь можно добавить отправку в систему мониторинга
            
        except Exception as e:
            logger.error(f'Failed to log security event: {str(e)}')
    
    @staticmethod
    def get_client_ip(request) -> str:
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
    
    @staticmethod
    def get_user_agent(request) -> str:
        """Получение User-Agent клиента"""
        return request.META.get('HTTP_USER_AGENT', '')
    
    @staticmethod
    def is_secure_connection(request) -> bool:
        """Проверка безопасного соединения"""
        return request.is_secure()
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions: List[str] = None, max_size_mb: int = 10) -> Dict[str, Any]:
        """Проверка загружаемого файла"""
        if allowed_extensions is None:
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
        
        errors = []
        
        # Проверка размера
        if file.size > max_size_mb * 1024 * 1024:
            errors.append(f'Размер файла не должен превышать {max_size_mb} МБ')
        
        # Проверка расширения
        file_extension = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
        if file_extension not in allowed_extensions:
            errors.append(f'Недопустимое расширение файла. Разрешены: {", ".join(allowed_extensions)}')
        
        # Проверка имени файла
        if not re.match(r'^[a-zA-Z0-9._-]+$', file.name):
            errors.append('Имя файла содержит недопустимые символы')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'file_info': {
                'name': file.name,
                'size': file.size,
                'extension': file_extension
            }
        }
    
    @staticmethod
    def clean_expired_security_data() -> Dict[str, int]:
        """Очистка устаревших данных безопасности"""
        try:
            # Очистка rate limit данных
            # Здесь можно реализовать логику очистки устаревших записей
            
            logger.info('Security data cleanup completed')
            return {
                'rate_limits_cleaned': 0,
                'blacklist_entries_cleaned': 0,
                'security_logs_cleaned': 0
            }
            
        except Exception as e:
            logger.error(f'Failed to clean security data: {str(e)}')
            return {
                'rate_limits_cleaned': 0,
                'blacklist_entries_cleaned': 0,
                'security_logs_cleaned': 0
            }