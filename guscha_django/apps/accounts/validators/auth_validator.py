from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from typing import Dict, Any, Optional, Tuple
import re
import logging
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthValidator:
    """Валидатор для аутентификации"""
    
    # Константы для валидации
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MAX_EMAIL_LENGTH = 254
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    def validate_login_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для входа"""
        errors = {}
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Валидация email
        if not email:
            errors['email'] = [_('Email обязателен')]
        else:
            try:
                self.validate_email_format(email)
            except ValidationError as e:
                errors['email'] = e.messages
        
        # Валидация пароля
        if not password:
            errors['password'] = [_('Пароль обязателен')]
        elif len(password) > self.MAX_PASSWORD_LENGTH:
            errors['password'] = [_('Пароль слишком длинный')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_email_format(self, email: str) -> None:
        """Валидация формата email"""
        if not email:
            raise ValidationError(_('Email обязателен'))
        
        if len(email) > self.MAX_EMAIL_LENGTH:
            raise ValidationError(
                _(f'Email не может быть длиннее {self.MAX_EMAIL_LENGTH} символов')
            )
        
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(_('Введите корректный email адрес'))
    
    def validate_password_reset_request_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для запроса сброса пароля"""
        errors = {}
        
        email = data.get('email', '').strip()
        
        if not email:
            errors['email'] = [_('Email обязателен')]
        else:
            try:
                self.validate_email_format(email)
            except ValidationError as e:
                errors['email'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_password_reset_confirm_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для подтверждения сброса пароля"""
        errors = {}
        
        uid = data.get('uid', '')
        token = data.get('token', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Валидация UID
        if not uid:
            errors['uid'] = [_('UID обязателен')]
        else:
            try:
                self.validate_uid(uid)
            except ValidationError as e:
                errors['uid'] = e.messages
        
        # Валидация токена
        if not token:
            errors['token'] = [_('Токен обязателен')]
        elif len(token) < 10:  # Минимальная длина токена
            errors['token'] = [_('Недействительный токен')]
        
        # Валидация нового пароля
        if not new_password:
            errors['new_password'] = [_('Новый пароль обязателен')]
        else:
            try:
                self.validate_password_strength(new_password)
            except ValidationError as e:
                errors['new_password'] = e.messages
        
        # Валидация подтверждения пароля
        if not confirm_password:
            errors['confirm_password'] = [_('Подтверждение пароля обязательно')]
        elif new_password != confirm_password:
            errors['confirm_password'] = [_('Пароли не совпадают')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_uid(self, uid: str) -> None:
        """Валидация UID для сброса пароля"""
        try:
            urlsafe_base64_decode(uid).decode()
        except (TypeError, ValueError):
            raise ValidationError(_('Недействительный UID'))
    
    def validate_password_strength(self, password: str) -> None:
        """Валидация силы пароля"""
        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                _(f'Пароль должен содержать минимум {self.MIN_PASSWORD_LENGTH} символов')
            )
        
        if len(password) > self.MAX_PASSWORD_LENGTH:
            raise ValidationError(
                _(f'Пароль не может быть длиннее {self.MAX_PASSWORD_LENGTH} символов')
            )
        
        # Проверка сложности пароля
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Пароль должен содержать хотя бы одну строчную букву'))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Пароль должен содержать хотя бы одну заглавную букву'))
        
        if not re.search(r'\d', password):
            raise ValidationError(_('Пароль должен содержать хотя бы одну цифру'))
        
        if not re.search(r'[@$!%*?&]', password):
            raise ValidationError(_('Пароль должен содержать хотя бы один специальный символ (@$!%*?&)'))
    
    def validate_change_password_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для смены пароля"""
        errors = {}
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Валидация старого пароля
        if not old_password:
            errors['old_password'] = [_('Текущий пароль обязателен')]
        
        # Валидация нового пароля
        if not new_password:
            errors['new_password'] = [_('Новый пароль обязателен')]
        else:
            try:
                self.validate_password_strength(new_password)
            except ValidationError as e:
                errors['new_password'] = e.messages
        
        # Валидация подтверждения пароля
        if not confirm_password:
            errors['confirm_password'] = [_('Подтверждение пароля обязательно')]
        elif new_password != confirm_password:
            errors['confirm_password'] = [_('Пароли не совпадают')]
        
        # Проверка, что новый пароль отличается от старого
        if old_password and new_password and old_password == new_password:
            errors['new_password'] = [_('Новый пароль должен отличаться от текущего')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_token_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных токена"""
        errors = {}
        
        token = data.get('token', '')
        
        if not token:
            errors['token'] = [_('Токен обязателен')]
        elif not isinstance(token, str):
            errors['token'] = [_('Токен должен быть строкой')]
        elif len(token) < 10:
            errors['token'] = [_('Недействительный токен')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_refresh_token_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для обновления токена"""
        errors = {}
        
        refresh_token = data.get('refresh', '')
        
        if not refresh_token:
            errors['refresh'] = [_('Refresh токен обязателен')]
        elif not isinstance(refresh_token, str):
            errors['refresh'] = [_('Refresh токен должен быть строкой')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_logout_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для выхода"""
        # Для выхода обычно не требуется дополнительная валидация
        # Но можно добавить проверку refresh токена если требуется
        pass
    
    def validate_user_activation_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для активации пользователя"""
        errors = {}
        
        uid = data.get('uid', '')
        token = data.get('token', '')
        
        if not uid:
            errors['uid'] = [_('UID обязателен')]
        else:
            try:
                self.validate_uid(uid)
            except ValidationError as e:
                errors['uid'] = e.messages
        
        if not token:
            errors['token'] = [_('Токен обязателен')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_session_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных сессии"""
        errors = {}
        
        # Проверка наличия необходимых данных сессии
        required_fields = ['user_id']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                errors[field] = [_(f'{field} обязателен в данных сессии')]
        
        # Валидация user_id
        user_id = data.get('user_id')
        if user_id is not None:
            if not isinstance(user_id, int) or user_id <= 0:
                errors['user_id'] = [_('user_id должен быть положительным числом')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_login_attempt_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных попытки входа"""
        errors = {}
        
        email = data.get('email', '').strip()
        ip_address = data.get('ip_address', '')
        user_agent = data.get('user_agent', '')
        
        if not email:
            errors['email'] = [_('Email обязателен')]
        else:
            try:
                self.validate_email_format(email)
            except ValidationError as e:
                errors['email'] = e.messages
        
        # IP адрес не обязателен, но если есть - проверяем формат
        if ip_address and not self.is_valid_ip(ip_address):
            errors['ip_address'] = [_('Недействительный IP адрес')]
        
        if errors:
            raise ValidationError(errors)
    
    def is_valid_ip(self, ip: str) -> bool:
        """Проверка валидности IP адреса"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def validate_security_question_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных контрольного вопроса"""
        errors = {}
        
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        
        if not question:
            errors['question'] = [_('Контрольный вопрос обязателен')]
        elif len(question) < 10:
            errors['question'] = [_('Контрольный вопрос должен содержать минимум 10 символов')]
        elif len(question) > 200:
            errors['question'] = [_('Контрольный вопрос не может быть длиннее 200 символов')]
        
        if not answer:
            errors['answer'] = [_('Ответ на контрольный вопрос обязателен')]
        elif len(answer) < 2:
            errors['answer'] = [_('Ответ должен содержать минимум 2 символа')]
        elif len(answer) > 100:
            errors['answer'] = [_('Ответ не может быть длиннее 100 символов')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_two_factor_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных двухфакторной аутентификации"""
        errors = {}
        
        code = data.get('code', '').strip()
        
        if not code:
            errors['code'] = [_('Код двухфакторной аутентификации обязателен')]
        elif not code.isdigit():
            errors['code'] = [_('Код должен содержать только цифры')]
        elif len(code) != 6:
            errors['code'] = [_('Код должен содержать 6 цифр')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_rate_limit_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Валидация ограничений по частоте запросов"""
        attempts = data.get('attempts', 0)
        last_attempt = data.get('last_attempt')
        
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            if last_attempt:
                lockout_until = last_attempt + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                if timezone.now() < lockout_until:
                    remaining_time = lockout_until - timezone.now()
                    minutes = int(remaining_time.total_seconds() / 60)
                    return False, _(f'Аккаунт заблокирован. Попробуйте через {minutes} минут')
        
        return True, ''
    
    def validate_device_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных устройства"""
        errors = {}
        
        device_id = data.get('device_id', '')
        device_name = data.get('device_name', '')
        
        if device_id and len(device_id) > 100:
            errors['device_id'] = [_('ID устройства не может быть длиннее 100 символов')]
        
        if device_name and len(device_name) > 200:
            errors['device_name'] = [_('Название устройства не может быть длиннее 200 символов')]
        
        if errors:
            raise ValidationError(errors)
    
    def is_secure_password(self, password: str) -> bool:
        """Проверка безопасности пароля"""
        try:
            self.validate_password_strength(password)
            return True
        except ValidationError:
            return False
    
    def get_password_security_score(self, password: str) -> int:
        """Получение оценки безопасности пароля (0-100)"""
        score = 0
        
        # Длина
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Символы
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'\d', password):
            score += 15
        if re.search(r'[@$!%*?&]', password):
            score += 15
        
        return min(score, 100)