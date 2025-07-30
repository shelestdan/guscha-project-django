from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, Optional, List
import re
import uuid
import logging

logger = logging.getLogger(__name__)


class QRValidator:
    """Валидатор для QR кодов"""
    
    # Константы для валидации
    MIN_QR_CODE_LENGTH = 8
    MAX_QR_CODE_LENGTH = 64
    MAX_QR_DATA_LENGTH = 2048
    MAX_QR_DESCRIPTION_LENGTH = 500
    MIN_EXPIRY_MINUTES = 1
    MAX_EXPIRY_MINUTES = 10080  # 7 дней
    MAX_SCAN_LIMIT = 1000
    
    # Допустимые типы QR кодов
    VALID_QR_TYPES = [
        'registration',
        'login',
        'password_reset',
        'account_verification',
        'telegram_link',
        'payment',
        'general'
    ]
    
    # Допустимые статусы QR кодов
    VALID_QR_STATUSES = [
        'active',
        'used',
        'expired',
        'cancelled',
        'pending'
    ]
    
    def validate_qr_code(self, qr_code: str) -> None:
        """Валидация QR кода"""
        if not qr_code:
            raise ValidationError(_('QR код обязателен'))
        
        if not isinstance(qr_code, str):
            raise ValidationError(_('QR код должен быть строкой'))
        
        if len(qr_code) < self.MIN_QR_CODE_LENGTH:
            raise ValidationError(
                _(f'QR код должен содержать минимум {self.MIN_QR_CODE_LENGTH} символов')
            )
        
        if len(qr_code) > self.MAX_QR_CODE_LENGTH:
            raise ValidationError(
                _(f'QR код не может быть длиннее {self.MAX_QR_CODE_LENGTH} символов')
            )
        
        # Проверяем формат (буквы, цифры, дефисы)
        if not re.match(r'^[A-Za-z0-9-_]+$', qr_code):
            raise ValidationError(
                _('QR код может содержать только буквы, цифры, дефисы и подчеркивания')
            )
    
    def validate_qr_type(self, qr_type: str) -> None:
        """Валидация типа QR кода"""
        if not qr_type:
            raise ValidationError(_('Тип QR кода обязателен'))
        
        if qr_type not in self.VALID_QR_TYPES:
            raise ValidationError(
                _(f'Недействительный тип QR кода. Допустимые: {", ".join(self.VALID_QR_TYPES)}')
            )
    
    def validate_qr_status(self, status: str) -> None:
        """Валидация статуса QR кода"""
        if not status:
            raise ValidationError(_('Статус QR кода обязателен'))
        
        if status not in self.VALID_QR_STATUSES:
            raise ValidationError(
                _(f'Недействительный статус QR кода. Допустимые: {", ".join(self.VALID_QR_STATUSES)}')
            )
    
    def validate_qr_data(self, data: str) -> None:
        """Валидация данных QR кода"""
        if data and len(data) > self.MAX_QR_DATA_LENGTH:
            raise ValidationError(
                _(f'Данные QR кода не могут быть длиннее {self.MAX_QR_DATA_LENGTH} символов')
            )
    
    def validate_qr_description(self, description: str) -> None:
        """Валидация описания QR кода"""
        if description and len(description) > self.MAX_QR_DESCRIPTION_LENGTH:
            raise ValidationError(
                _(f'Описание QR кода не может быть длиннее {self.MAX_QR_DESCRIPTION_LENGTH} символов')
            )
    
    def validate_expiry_minutes(self, minutes: int) -> None:
        """Валидация времени истечения в минутах"""
        if not isinstance(minutes, int):
            raise ValidationError(_('Время истечения должно быть числом'))
        
        if minutes < self.MIN_EXPIRY_MINUTES:
            raise ValidationError(
                _(f'Время истечения должно быть минимум {self.MIN_EXPIRY_MINUTES} минут')
            )
        
        if minutes > self.MAX_EXPIRY_MINUTES:
            raise ValidationError(
                _(f'Время истечения не может быть больше {self.MAX_EXPIRY_MINUTES} минут')
            )
    
    def validate_scan_limit(self, limit: int) -> None:
        """Валидация лимита сканирований"""
        if limit is not None:
            if not isinstance(limit, int) or limit < 1:
                raise ValidationError(_('Лимит сканирований должен быть положительным числом'))
            
            if limit > self.MAX_SCAN_LIMIT:
                raise ValidationError(
                    _(f'Лимит сканирований не может быть больше {self.MAX_SCAN_LIMIT}')
                )
    
    def validate_qr_creation_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для создания QR кода"""
        errors = {}
        
        qr_type = data.get('type', '').strip()
        description = data.get('description', '').strip()
        qr_data = data.get('data', '')
        expiry_minutes = data.get('expiry_minutes', 60)
        scan_limit = data.get('scan_limit')
        
        # Валидация типа
        if not qr_type:
            errors['type'] = [_('Тип QR кода обязателен')]
        else:
            try:
                self.validate_qr_type(qr_type)
            except ValidationError as e:
                errors['type'] = e.messages
        
        # Валидация описания
        if description:
            try:
                self.validate_qr_description(description)
            except ValidationError as e:
                errors['description'] = e.messages
        
        # Валидация данных
        if qr_data:
            try:
                self.validate_qr_data(qr_data)
            except ValidationError as e:
                errors['data'] = e.messages
        
        # Валидация времени истечения
        try:
            self.validate_expiry_minutes(expiry_minutes)
        except ValidationError as e:
            errors['expiry_minutes'] = e.messages
        
        # Валидация лимита сканирований
        if scan_limit is not None:
            try:
                self.validate_scan_limit(scan_limit)
            except ValidationError as e:
                errors['scan_limit'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_scan_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для сканирования QR кода"""
        errors = {}
        
        qr_code = data.get('qr_code', '').strip()
        user_agent = data.get('user_agent', '').strip()
        ip_address = data.get('ip_address', '').strip()
        
        # Валидация QR кода
        if not qr_code:
            errors['qr_code'] = [_('QR код обязателен')]
        else:
            try:
                self.validate_qr_code(qr_code)
            except ValidationError as e:
                errors['qr_code'] = e.messages
        
        # Валидация IP адреса (опционально)
        if ip_address and not self.is_valid_ip(ip_address):
            errors['ip_address'] = [_('Недействительный IP адрес')]
        
        # Валидация User Agent (опционально)
        if user_agent and len(user_agent) > 500:
            errors['user_agent'] = [_('User Agent не может быть длиннее 500 символов')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_trigger_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для активации QR кода"""
        errors = {}
        
        qr_code = data.get('qr_code', '').strip()
        chat_id = data.get('chat_id')
        
        # Валидация QR кода
        if not qr_code:
            errors['qr_code'] = [_('QR код обязателен')]
        else:
            try:
                self.validate_qr_code(qr_code)
            except ValidationError as e:
                errors['qr_code'] = e.messages
        
        # Валидация chat_id
        if chat_id is not None:
            from .telegram_validator import TelegramValidator
            telegram_validator = TelegramValidator()
            try:
                telegram_validator.validate_chat_id(chat_id)
            except ValidationError as e:
                errors['chat_id'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_registration_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для регистрации через QR код"""
        errors = {}
        
        qr_code = data.get('qr_code', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Валидация QR кода
        if not qr_code:
            errors['qr_code'] = [_('QR код обязателен')]
        else:
            try:
                self.validate_qr_code(qr_code)
            except ValidationError as e:
                errors['qr_code'] = e.messages
        
        # Валидация email
        if not email:
            errors['email'] = [_('Email обязателен')]
        else:
            from .auth_validator import AuthValidator
            auth_validator = AuthValidator()
            try:
                auth_validator.validate_email_format(email)
            except ValidationError as e:
                errors['email'] = e.messages
        
        # Валидация пароля
        if not password:
            errors['password'] = [_('Пароль обязателен')]
        else:
            from .auth_validator import AuthValidator
            auth_validator = AuthValidator()
            try:
                auth_validator.validate_password_strength(password)
            except ValidationError as e:
                errors['password'] = e.messages
        
        # Валидация имени
        if first_name and len(first_name) > 150:
            errors['first_name'] = [_('Имя не может быть длиннее 150 символов')]
        
        if last_name and len(last_name) > 150:
            errors['last_name'] = [_('Фамилия не может быть длиннее 150 символов')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_update_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для обновления QR кода"""
        errors = {}
        
        status = data.get('status', '').strip()
        description = data.get('description', '').strip()
        qr_data = data.get('data', '')
        scan_limit = data.get('scan_limit')
        
        # Валидация статуса
        if status:
            try:
                self.validate_qr_status(status)
            except ValidationError as e:
                errors['status'] = e.messages
        
        # Валидация описания
        if description:
            try:
                self.validate_qr_description(description)
            except ValidationError as e:
                errors['description'] = e.messages
        
        # Валидация данных
        if qr_data:
            try:
                self.validate_qr_data(qr_data)
            except ValidationError as e:
                errors['data'] = e.messages
        
        # Валидация лимита сканирований
        if scan_limit is not None:
            try:
                self.validate_scan_limit(scan_limit)
            except ValidationError as e:
                errors['scan_limit'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_search_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для поиска QR кодов"""
        errors = {}
        
        qr_type = data.get('type', '').strip()
        status = data.get('status', '').strip()
        limit = data.get('limit', 50)
        offset = data.get('offset', 0)
        
        # Валидация типа
        if qr_type:
            try:
                self.validate_qr_type(qr_type)
            except ValidationError as e:
                errors['type'] = e.messages
        
        # Валидация статуса
        if status:
            try:
                self.validate_qr_status(status)
            except ValidationError as e:
                errors['status'] = e.messages
        
        # Валидация лимита
        if not isinstance(limit, int) or limit < 1:
            errors['limit'] = [_('Лимит должен быть положительным числом')]
        elif limit > 1000:
            errors['limit'] = [_('Лимит не может быть больше 1000')]
        
        # Валидация смещения
        if not isinstance(offset, int) or offset < 0:
            errors['offset'] = [_('Смещение должно быть неотрицательным числом')]
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_statistics_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для статистики QR кодов"""
        errors = {}
        
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        qr_type = data.get('type', '').strip()
        
        # Валидация дат
        if date_from and date_to:
            if date_from > date_to:
                errors['date_range'] = [_('Дата начала не может быть больше даты окончания')]
        
        # Валидация типа
        if qr_type:
            try:
                self.validate_qr_type(qr_type)
            except ValidationError as e:
                errors['type'] = e.messages
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_cleanup_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для очистки QR кодов"""
        errors = {}
        
        days_old = data.get('days_old', 0)
        status_filter = data.get('status_filter', []).copy() if data.get('status_filter') else []
        
        # Валидация количества дней
        if not isinstance(days_old, int) or days_old < 0:
            errors['days_old'] = [_('Количество дней должно быть неотрицательным числом')]
        elif days_old > 365:
            errors['days_old'] = [_('Количество дней не может быть больше 365')]
        
        # Валидация фильтра статусов
        if status_filter:
            if not isinstance(status_filter, list):
                errors['status_filter'] = [_('Фильтр статусов должен быть списком')]
            else:
                for status in status_filter:
                    try:
                        self.validate_qr_status(status)
                    except ValidationError:
                        errors['status_filter'] = [_(f'Недействительный статус: {status}')]
                        break
        
        if errors:
            raise ValidationError(errors)
    
    def validate_qr_bulk_update_data(self, data: Dict[str, Any]) -> None:
        """Валидация данных для массового обновления QR кодов"""
        errors = {}
        
        qr_codes = data.get('qr_codes', [])
        update_data = data.get('update_data', {})
        
        # Валидация списка QR кодов
        if not qr_codes:
            errors['qr_codes'] = [_('Список QR кодов обязателен')]
        elif not isinstance(qr_codes, list):
            errors['qr_codes'] = [_('QR коды должны быть списком')]
        elif len(qr_codes) > 100:
            errors['qr_codes'] = [_('Нельзя обновить более 100 QR кодов за раз')]
        else:
            for i, qr_code in enumerate(qr_codes):
                try:
                    self.validate_qr_code(qr_code)
                except ValidationError:
                    errors['qr_codes'] = [_(f'Недействительный QR код в позиции {i + 1}')]
                    break
        
        # Валидация данных для обновления
        if update_data:
            try:
                self.validate_qr_update_data(update_data)
            except ValidationError as e:
                errors['update_data'] = e.message_dict if hasattr(e, 'message_dict') else [str(e)]
        
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
    
    def validate_qr_id(self, qr_id) -> None:
        """Валидация QR ID (UUID)"""
        if not qr_id:
            raise ValidationError(_('QR ID обязателен'))
        
        # Принимаем как строки, так и UUID объекты
        if isinstance(qr_id, uuid.UUID):
            return  # UUID объект уже валиден
        
        if not isinstance(qr_id, str):
            raise ValidationError(_('QR ID должен быть строкой или UUID объектом'))
        
        try:
            uuid.UUID(qr_id)
        except ValueError:
            raise ValidationError(_('QR ID должен быть валидным UUID'))
    
    def is_valid_qr_code(self, qr_code: str) -> bool:
        """Проверка валидности QR кода"""
        try:
            self.validate_qr_code(qr_code)
            return True
        except ValidationError:
            return False
    
    def is_valid_qr_type(self, qr_type: str) -> bool:
        """Проверка валидности типа QR кода"""
        return qr_type in self.VALID_QR_TYPES
    
    def is_valid_qr_status(self, status: str) -> bool:
        """Проверка валидности статуса QR кода"""
        return status in self.VALID_QR_STATUSES
    
    def generate_qr_code(self, length: int = 32) -> str:
        """Генерация уникального QR кода"""
        if length < self.MIN_QR_CODE_LENGTH:
            length = self.MIN_QR_CODE_LENGTH
        elif length > self.MAX_QR_CODE_LENGTH:
            length = self.MAX_QR_CODE_LENGTH
        
        # Генерируем UUID и берем нужное количество символов
        qr_uuid = str(uuid.uuid4()).replace('-', '')
        
        if len(qr_uuid) >= length:
            return qr_uuid[:length].upper()
        else:
            # Если UUID короче нужной длины, дополняем случайными символами
            import random
            import string
            additional_chars = ''.join(
                random.choice(string.ascii_uppercase + string.digits) 
                for _ in range(length - len(qr_uuid))
            )
            return (qr_uuid + additional_chars).upper()
    
    def sanitize_qr_data(self, data: str) -> str:
        """Очистка и нормализация данных QR кода"""
        if not data:
            return ''
        
        # Убираем лишние пробелы
        data = data.strip()
        
        # Ограничиваем длину
        if len(data) > self.MAX_QR_DATA_LENGTH:
            data = data[:self.MAX_QR_DATA_LENGTH]
        
        return data
    
    def get_qr_type_display_name(self, qr_type: str) -> str:
        """Получение отображаемого имени типа QR кода"""
        type_names = {
            'registration': _('Регистрация'),
            'login': _('Вход'),
            'password_reset': _('Сброс пароля'),
            'account_verification': _('Верификация аккаунта'),
            'telegram_link': _('Привязка Telegram'),
            'payment': _('Платеж'),
            'general': _('Общий')
        }
        return type_names.get(qr_type, qr_type)
    
    def get_qr_status_display_name(self, status: str) -> str:
        """Получение отображаемого имени статуса QR кода"""
        status_names = {
            'active': _('Активный'),
            'used': _('Использован'),
            'expired': _('Истек'),
            'cancelled': _('Отменен'),
            'pending': _('Ожидает')
        }
        return status_names.get(status, status)