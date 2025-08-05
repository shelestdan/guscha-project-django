from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class TelegramValidator:
    """Валидатор для Telegram интеграции"""
    
    # Константы для валидации
    MIN_VERIFICATION_CODE_LENGTH = 4
    MAX_VERIFICATION_CODE_LENGTH = 8
    MAX_TELEGRAM_USERNAME_LENGTH = 32
    MAX_CHAT_ID_LENGTH = 20
    MAX_MESSAGE_LENGTH = 4096  # Лимит Telegram
    MIN_CHAT_ID = -999999999999
    MAX_CHAT_ID = 999999999999
    
    def validate_telegram_username(self, username: str) -> None:
        """Валидация Telegram username"""
        if not username:
            raise ValidationError(_('Telegram username обязателен'))
        
        # Убираем @ если есть
        username = username.lstrip('@')
        
        if len(username) < 5:
            raise ValidationError(_('Telegram username должен содержать минимум 5 символов'))
        
        if len(username) > self.MAX_TELEGRAM_USERNAME_LENGTH:
            raise ValidationError(
                _(f'Telegram username не может быть длиннее {self.MAX_TELEGRAM_USERNAME_LENGTH} символов')
            )
        
        # Проверка формата username
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', username):
            raise ValidationError(
                _('Telegram username может содержать только буквы, цифры и подчеркивания, '
                  'должен начинаться с буквы')
            )
    
    def validate_chat_id(self, chat_id: Any) -> None:
        """Валидация Telegram chat ID (обязательный)"""
        if chat_id is None or chat_id == '':
            raise ValidationError(_('Chat ID обязателен'))
        
        self._validate_chat_id_format(chat_id)
    
    def validate_chat_id_optional(self, chat_id: Any) -> None:
        """Валидация Telegram chat ID (опциональный для QR-кодов)"""
        if chat_id is None or chat_id == '':
            return  # Для QR-кодов chat_id может быть пустым
        
        self._validate_chat_id_format(chat_id)
    
    def _validate_chat_id_format(self, chat_id: Any) -> None:
        """Внутренний метод для валидации формата chat ID"""
        # Преобразуем в int если это строка
        try:
            chat_id_int = int(chat_id)
        except (ValueError, TypeError):
            raise ValidationError(_('Chat ID должен быть числом'))
        
        if chat_id_int < self.MIN_CHAT_ID or chat_id_int > self.MAX_CHAT_ID:
            raise ValidationError(_('Недействительный Chat ID'))
    
    def validate_verification_code(self, code: str) -> None:
        """Валидация кода верификации"""
        if not code:
            raise ValidationError(_('Код верификации обязателен'))
        
        if not isinstance(code, str):
            raise ValidationError(_('Код верификации должен быть строкой'))
        
        if len(code) < self.MIN_VERIFICATION_CODE_LENGTH:
            raise ValidationError(
                _(f'Код верификации должен содержать минимум {self.MIN_VERIFICATION_CODE_LENGTH} символов')
            )
        
        if len(code) > self.MAX_VERIFICATION_CODE_LENGTH:
            raise ValidationError(
                _(f'Код верификации не может быть длиннее {self.MAX_VERIFICATION_CODE_LENGTH} символов')
            )
        
        # Проверяем, что код содержит только цифры и буквы
        if not re.match(r'^[A-Za-z0-9]+$', code):
            raise ValidationError(_('Код верификации может содержать только буквы и цифры'))
    
    def validate_verification_type(self, verification_type: str) -> None:
        """Валидация типа верификации"""
        if not verification_type:
            raise ValidationError(_('Тип верификации обязателен'))
        
        if not isinstance(verification_type, str):
            raise ValidationError(_('Тип верификации должен быть строкой'))
        
        valid_types = ['registration', 'password_reset', 'login', 'link_account', 'qr_code', 'qr_registration']
        if verification_type not in valid_types:
            raise ValidationError(
                _(f'Недействительный тип верификации. Допустимые: {", ".join(valid_types)}')
            )
    
    def validate_telegram_message(self, message: str) -> None:
        """Валидация Telegram сообщения"""
        if not message:
            raise ValidationError(_('Сообщение не может быть пустым'))
        
        if len(message) > self.MAX_MESSAGE_LENGTH:
            raise ValidationError(
                _(f'Сообщение не может быть длиннее {self.MAX_MESSAGE_LENGTH} символов')
            )
    
    def validate_telegram_link_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для привязки Telegram аккаунта"""
        errors = {}
        
        chat_id = data.get('chat_id')
        username = data.get('username', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # Валидация chat_id
        if chat_id is not None:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация username (опционально)
        if username:
            try:
                self.validate_telegram_username(username)
            except ValidationError as e:
                errors['username'] = e.messages
        
        # Валидация кода верификации
        if verification_code:
            try:
                self.validate_verification_code(verification_code)
            except ValidationError as e:
                errors['verification_code'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_unlink_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для отвязки Telegram аккаунта"""
        errors = {}
        
        # Для отвязки обычно не требуется дополнительных данных
        # Но можно добавить подтверждение
        confirm = data.get('confirm', False)
        
        if not confirm:
            errors['confirm'] = [_('Подтвердите отвязку Telegram аккаунта')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_registration_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для регистрации через Telegram"""
        errors = {}
        
        chat_id = data.get('chat_id')
        username = data.get('username', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # Валидация chat_id (обязательно)
        if not chat_id:
            errors['chat_id'] = [_('Chat ID обязателен')]
        else:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация username (опционально)
        if username:
            try:
                self.validate_telegram_username(username)
            except ValidationError as e:
                errors['username'] = e.messages
        
        # Валидация имени
        if first_name and len(first_name) > 64:
            errors['first_name'] = [_('Имя не может быть длиннее 64 символов')]
        
        if last_name and len(last_name) > 64:
            errors['last_name'] = [_('Фамилия не может быть длиннее 64 символов')]
        
        # Валидация кода верификации
        if verification_code:
            try:
                self.validate_verification_code(verification_code)
            except ValidationError as e:
                errors['verification_code'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_password_reset_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для сброса пароля через Telegram"""
        errors = {}
        
        chat_id = data.get('chat_id')
        verification_code = data.get('verification_code', '').strip()
        new_password = data.get('new_password', '')
        
        # Валидация chat_id
        if not chat_id:
            errors['chat_id'] = [_('Chat ID обязателен')]
        else:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация кода верификации
        if not verification_code:
            errors['verification_code'] = [_('Код верификации обязателен')]
        else:
            try:
                self.validate_verification_code(verification_code)
            except ValidationError as e:
                errors['verification_code'] = e.messages
        
        # Валидация нового пароля (если предоставлен)
        if new_password:
            from .auth_validator import AuthValidator
            auth_validator = AuthValidator()
            try:
                auth_validator.validate_password_strength(new_password)
            except ValidationError as e:
                errors['new_password'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_code_generation_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для генерации кода верификации"""
        errors = {}
        
        chat_id = data.get('chat_id')
        code_type = data.get('code_type', '').strip()
        
        # Валидация chat_id
        if not chat_id:
            errors['chat_id'] = [_('Chat ID обязателен')]
        else:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация типа кода
        valid_code_types = ['registration', 'password_reset', 'login', 'link_account']
        if not code_type:
            errors['code_type'] = [_('Тип кода обязателен')]
        elif code_type not in valid_code_types:
            errors['code_type'] = [_(f'Недействительный тип кода. Допустимые: {", ".join(valid_code_types)}')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_code_verification_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для верификации кода"""
        errors = {}
        
        chat_id = data.get('chat_id')
        verification_code = data.get('verification_code', '').strip()
        code_type = data.get('code_type', '').strip()
        
        # Валидация chat_id
        if not chat_id:
            errors['chat_id'] = [_('Chat ID обязателен')]
        else:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация кода верификации
        if not verification_code:
            errors['verification_code'] = [_('Код верификации обязателен')]
        else:
            try:
                self.validate_verification_code(verification_code)
            except ValidationError as e:
                errors['verification_code'] = e.messages
        
        # Валидация типа кода (опционально)
        if code_type:
            valid_code_types = ['registration', 'password_reset', 'login', 'link_account']
            if code_type not in valid_code_types:
                errors['code_type'] = [_(f'Недействительный тип кода. Допустимые: {", ".join(valid_code_types)}')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_bot_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных Telegram бота"""
        errors = {}
        
        bot_token = data.get('bot_token', '').strip()
        webhook_url = data.get('webhook_url', '').strip()
        
        # Валидация токена бота
        if bot_token:
            if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', bot_token):
                errors['bot_token'] = [_('Недействительный формат токена бота')]
        
        # Валидация webhook URL
        if webhook_url:
            if not webhook_url.startswith('https://'):
                errors['webhook_url'] = [_('Webhook URL должен использовать HTTPS')]
            elif len(webhook_url) > 256:
                errors['webhook_url'] = [_('Webhook URL не может быть длиннее 256 символов')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_statistics_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для статистики Telegram"""
        errors = {}
        
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        # Валидация дат
        if date_from and date_to:
            if date_from > date_to:
                errors['date_range'] = [_('Дата начала не может быть больше даты окончания')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_cleanup_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для очистки Telegram данных"""
        errors = {}
        
        days_old = data.get('days_old', 0)
        
        if not isinstance(days_old, int) or days_old < 0:
            errors['days_old'] = [_('Количество дней должно быть положительным числом')]
        elif days_old > 365:
            errors['days_old'] = [_('Количество дней не может быть больше 365')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_notification_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для уведомлений Telegram"""
        errors = {}
        
        chat_id = data.get('chat_id')
        message = data.get('message', '').strip()
        parse_mode = data.get('parse_mode', '').strip()
        
        # Валидация chat_id
        if not chat_id:
            errors['chat_id'] = [_('Chat ID обязателен')]
        else:
            try:
                self.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        # Валидация сообщения
        if not message:
            errors['message'] = [_('Сообщение обязательно')]
        else:
            try:
                self.validate_telegram_message(message)
            except ValidationError as e:
                errors['message'] = e.messages
        
        # Валидация режима парсинга
        if parse_mode:
            valid_parse_modes = ['Markdown', 'MarkdownV2', 'HTML']
            if parse_mode not in valid_parse_modes:
                errors['parse_mode'] = [_(f'Недействительный режим парсинга. Допустимые: {", ".join(valid_parse_modes)}')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_telegram_webhook_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных webhook Telegram"""
        errors = {}
        
        update_id = data.get('update_id')
        message = data.get('message', {})
        
        # Валидация update_id
        if update_id is not None:
            if not isinstance(update_id, int) or update_id < 0:
                errors['update_id'] = [_('Update ID должен быть положительным числом')]
        
        # Валидация сообщения
        if message:
            chat = message.get('chat', {})
            if chat:
                chat_id = chat.get('id')
                if chat_id is not None:
                    try:
                        self.validate_chat_id(chat_id)
                    except ValidationError as e:
                        errors['chat_id'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def is_valid_telegram_username(self, username: str) -> bool:
        """Проверка валидности Telegram username"""
        try:
            self.validate_telegram_username(username)
            return True
        except ValidationError:
            return False
    
    def is_valid_chat_id(self, chat_id: Any) -> bool:
        """Проверка валидности chat ID"""
        try:
            self.validate_chat_id(chat_id)
            return True
        except ValidationError:
            return False
    
    def is_valid_verification_code(self, code: str) -> bool:
        """Проверка валидности кода верификации"""
        try:
            self.validate_verification_code(code)
            return True
        except ValidationError:
            return False
    
    def sanitize_telegram_username(self, username: str) -> str:
        """Очистка и нормализация Telegram username"""
        if not username:
            return ''
        
        # Убираем @ если есть
        username = username.lstrip('@')
        
        # Убираем недопустимые символы
        username = re.sub(r'[^a-zA-Z0-9_]', '', username)
        
        return username
    
    def format_chat_id(self, chat_id: Any) -> Optional[int]:
        """Форматирование chat ID"""
        try:
            return int(chat_id)
        except (ValueError, TypeError):
            return None
    
    def generate_verification_code(self, length: int = 6) -> str:
        """Генерация кода верификации"""
        import secrets
        import string
        
        if length < self.MIN_VERIFICATION_CODE_LENGTH:
            length = self.MIN_VERIFICATION_CODE_LENGTH
        elif length > self.MAX_VERIFICATION_CODE_LENGTH:
            length = self.MAX_VERIFICATION_CODE_LENGTH
        
        # Генерируем код из цифр и заглавных букв
        characters = string.digits + string.ascii_uppercase
        return ''.join(secrets.choice(characters) for _ in range(length))