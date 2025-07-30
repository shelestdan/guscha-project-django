from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, List, Optional
import re
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserValidator:
    """Валидатор для пользователей"""
    
    # Константы для валидации
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 150
    MAX_EMAIL_LENGTH = 254
    
    # Регулярные выражения
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    )
    NAME_PATTERN = re.compile(r'^[a-zA-Zа-яА-ЯёЁ\s\-\']+$')
    TELEGRAM_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
    
    def validate_email(self, email: str) -> None:
        """Валидация email"""
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
        
        # Проверка на существование
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('Пользователь с таким email уже существует'))
    
    def validate_email_for_update(self, email: str, user_id: Optional[int] = None) -> None:
        """Валидация email для обновления (исключая текущего пользователя)"""
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
        
        # Проверка на существование (исключая текущего пользователя)
        queryset = User.objects.filter(email=email)
        if user_id:
            queryset = queryset.exclude(id=user_id)
        
        if queryset.exists():
            raise ValidationError(_('Пользователь с таким email уже существует'))
    
    def validate_password(self, password: str) -> None:
        """Валидация пароля"""
        if not password:
            raise ValidationError(_('Пароль обязателен'))
        
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
        
        # Проверка на распространенные пароли
        common_passwords = [
            'password', '12345678', 'qwerty123', 'admin123',
            'password123', '123456789', 'qwertyuiop'
        ]
        
        if password.lower() in common_passwords:
            raise ValidationError(_('Пароль слишком простой. Выберите более сложный пароль'))
    
    def validate_name(self, name: str, field_name: str = 'имя') -> None:
        """Валидация имени/фамилии"""
        if name and len(name) < self.MIN_NAME_LENGTH:
            raise ValidationError(
                _(f'{field_name.capitalize()} должно содержать минимум {self.MIN_NAME_LENGTH} символ')
            )
        
        if name and len(name) > self.MAX_NAME_LENGTH:
            raise ValidationError(
                _(f'{field_name.capitalize()} не может быть длиннее {self.MAX_NAME_LENGTH} символов')
            )
        
        if name and not self.NAME_PATTERN.match(name):
            raise ValidationError(
                _(f'{field_name.capitalize()} может содержать только буквы, пробелы, дефисы и апострофы')
            )
    
    def validate_first_name(self, first_name: str) -> None:
        """Валидация имени"""
        self.validate_name(first_name, 'имя')
    
    def validate_last_name(self, last_name: str) -> None:
        """Валидация фамилии"""
        self.validate_name(last_name, 'фамилия')
    
    def validate_telegram_username(self, username: str) -> None:
        """Валидация Telegram username"""
        if not username:
            return  # Telegram username не обязателен
        
        if not self.TELEGRAM_USERNAME_PATTERN.match(username):
            raise ValidationError(
                _('Telegram username должен содержать от 5 до 32 символов '
                  'и может включать только буквы, цифры и подчеркивания')
            )
    
    def validate_telegram_chat_id(self, chat_id: str) -> None:
        """Валидация Telegram chat ID"""
        if not chat_id:
            return  # Chat ID может быть пустым
        
        # Chat ID должен быть числом (может быть отрицательным для групп)
        try:
            int(chat_id)
        except ValueError:
            raise ValidationError(_('Telegram chat ID должен быть числом'))
        
        # Проверка на существование
        if User.objects.filter(telegram_chat_id=chat_id).exists():
            raise ValidationError(_('Этот Telegram аккаунт уже привязан к другому пользователю'))
    
    def validate_telegram_chat_id_for_update(
        self, 
        chat_id: str, 
        user_id: Optional[int] = None
    ) -> None:
        """Валидация Telegram chat ID для обновления"""
        if not chat_id:
            return
        
        try:
            int(chat_id)
        except ValueError:
            raise ValidationError(_('Telegram chat ID должен быть числом'))
        
        # Проверка на существование (исключая текущего пользователя)
        queryset = User.objects.filter(telegram_chat_id=chat_id)
        if user_id:
            queryset = queryset.exclude(id=user_id)
        
        if queryset.exists():
            raise ValidationError(_('Этот Telegram аккаунт уже привязан к другому пользователю'))
    
    def validate_user_creation_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для создания пользователя"""
        errors = {}
        
        try:
            self.validate_email(data.get('email', ''))
        except ValidationError as e:
            errors['email'] = e.messages
        
        try:
            self.validate_password(data.get('password', ''))
        except ValidationError as e:
            errors['password'] = e.messages
        
        try:
            self.validate_first_name(data.get('first_name', ''))
        except ValidationError as e:
            errors['first_name'] = e.messages
        
        try:
            self.validate_last_name(data.get('last_name', ''))
        except ValidationError as e:
            errors['last_name'] = e.messages
        
        try:
            self.validate_telegram_username(data.get('telegram_username', ''))
        except ValidationError as e:
            errors['telegram_username'] = e.messages
        
        try:
            self.validate_telegram_chat_id(data.get('telegram_chat_id', ''))
        except ValidationError as e:
            errors['telegram_chat_id'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_user_update_data(
        self, 
        data: Dict[str, Any], 
        user_id: int
    ) -> None:
        """Валидация данных для обновления пользователя"""
        errors = {}
        
        if 'email' in data:
            try:
                self.validate_email_for_update(data['email'], user_id)
            except ValidationError as e:
                errors['email'] = e.messages
        
        if 'password' in data:
            try:
                self.validate_password(data['password'])
            except ValidationError as e:
                errors['password'] = e.messages
        
        if 'first_name' in data:
            try:
                self.validate_first_name(data['first_name'])
            except ValidationError as e:
                errors['first_name'] = e.messages
        
        if 'last_name' in data:
            try:
                self.validate_last_name(data['last_name'])
            except ValidationError as e:
                errors['last_name'] = e.messages
        
        if 'telegram_username' in data:
            try:
                self.validate_telegram_username(data['telegram_username'])
            except ValidationError as e:
                errors['telegram_username'] = e.messages
        
        if 'telegram_chat_id' in data:
            try:
                self.validate_telegram_chat_id_for_update(data['telegram_chat_id'], user_id)
            except ValidationError as e:
                errors['telegram_chat_id'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_password_change_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для смены пароля"""
        errors = {}
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not old_password:
            errors['old_password'] = [_('Текущий пароль обязателен')]
        
        try:
            self.validate_password(new_password)
        except ValidationError as e:
            errors['new_password'] = e.messages
        
        if new_password != confirm_password:
            errors['confirm_password'] = [_('Пароли не совпадают')]
        
        if old_password == new_password:
            errors['new_password'] = [_('Новый пароль должен отличаться от текущего')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_bulk_operation_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для массовых операций"""
        errors = {}
        
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            errors['user_ids'] = [_('Список пользователей не может быть пустым')]
        
        if not isinstance(user_ids, list):
            errors['user_ids'] = [_('user_ids должен быть списком')]
        
        # Проверка, что все ID являются числами
        for user_id in user_ids:
            if not isinstance(user_id, int) or user_id <= 0:
                errors['user_ids'] = [_('Все ID пользователей должны быть положительными числами')]
                break
        
        if errors:
            raise ValidationError(errors)
    
    def validate_search_query(self, query: str) -> None:
        """Валидация поискового запроса"""
        if not query:
            raise ValidationError(_('Поисковый запрос не может быть пустым'))
        
        if len(query) < 2:
            raise ValidationError(_('Поисковый запрос должен содержать минимум 2 символа'))
        
        if len(query) > 100:
            raise ValidationError(_('Поисковый запрос не может быть длиннее 100 символов'))
    
    def validate_pending_registration_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для ожидающей регистрации"""
        errors = {}
        
        try:
            self.validate_email(data.get('email', ''))
        except ValidationError as e:
            errors['email'] = e.messages
        
        try:
            self.validate_first_name(data.get('first_name', ''))
        except ValidationError as e:
            errors['first_name'] = e.messages
        
        try:
            self.validate_last_name(data.get('last_name', ''))
        except ValidationError as e:
            errors['last_name'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def is_strong_password(self, password: str) -> bool:
        """Проверка силы пароля"""
        try:
            self.validate_password(password)
            return True
        except ValidationError:
            return False
    
    def get_password_strength_score(self, password: str) -> int:
        """Получение оценки силы пароля (0-100)"""
        score = 0
        
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'\d', password):
            score += 15
        if re.search(r'[@$!%*?&]', password):
            score += 15
        
        # Дополнительные символы
        if re.search(r'[^a-zA-Z0-9@$!%*?&]', password):
            score += 10
        
        return min(score, 100)