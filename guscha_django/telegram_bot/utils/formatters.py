"""Форматтеры для Telegram бота."""

import re
from typing import Dict, Any, Optional
from ..config.messages import messages


class MessageFormatter:
    """Форматтер сообщений для Telegram."""
    
    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """Экранирует специальные символы для MarkdownV2."""
        # Символы, которые нужно экранировать в MarkdownV2
        special_chars = r'_*[]()~`>#+-=|{}.!'
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def escape_code_for_spoiler(code: str) -> str:
        """Экранирует код для использования внутри spoiler-тегов ||...||."""
        # Внутри spoiler-тегов нужно экранировать все специальные символы MarkdownV2
        # включая символ '-' который вызывает ошибку
        special_chars = r'_*[]()~`>#+-=|{}.!'
        
        for char in special_chars:
            code = code.replace(char, f'\\{char}')
        
        return code
    
    @staticmethod
    def format_phone_display(phone: str) -> str:
        """Форматирует номер телефона для отображения."""
        if not phone:
            return ""
        
        # Убираем все кроме цифр и +
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Форматируем российские номера
        if clean_phone.startswith('+7') and len(clean_phone) == 12:
            return f"+7 ({clean_phone[2:5]}) {clean_phone[5:8]}-{clean_phone[8:10]}-{clean_phone[10:12]}"
        
        # Для других номеров возвращаем как есть
        return clean_phone
    
    @classmethod
    def format_verification_code_message(
        cls, 
        code: str, 
        verification_type: str, 
        timeout_minutes: int = 10
    ) -> str:
        """Форматирует сообщение с кодом верификации."""
        verification_type_display = messages.get_verification_type_display(verification_type)
        
        # Экранируем код для использования внутри spoiler-тегов
        escaped_code = cls.escape_code_for_spoiler(code)
        
        # Экранируем verification_type для MarkdownV2
        escaped_verification_type = cls.escape_markdown_v2(verification_type_display)
        
        return messages.format_message(
            messages.VERIFICATION_CODE,
            code=escaped_code,
            verification_type=escaped_verification_type,
            timeout=timeout_minutes
        )
    
    @classmethod
    def format_phone_confirmed_message(
        cls,
        code: str,
        verification_type: str,
        timeout_minutes: int = 10
    ) -> str:
        """Форматирует сообщение о подтверждении номера телефона."""
        verification_type_display = messages.get_verification_type_display(verification_type)
        
        # Экранируем код для использования внутри spoiler-тегов
        escaped_code = cls.escape_code_for_spoiler(code)
        
        # Экранируем verification_type для MarkdownV2
        escaped_verification_type = cls.escape_markdown_v2(verification_type_display)
        
        return messages.format_message(
            messages.PHONE_CONFIRMED,
            code=escaped_code,
            verification_type=escaped_verification_type,
            timeout=timeout_minutes
        )
    
    @classmethod
    def format_welcome_message(
        cls,
        first_name: str,
        verification_type: Optional[str] = None,
        is_qr_code: bool = False
    ) -> str:
        """Форматирует приветственное сообщение."""
        if is_qr_code:
            return messages.format_message(
                messages.WELCOME_QR_SUCCESS,
                first_name=first_name
            )
        elif verification_type:
            verification_type_display = messages.get_verification_type_display(verification_type)
            return messages.format_message(
                messages.WELCOME_WITH_CODE,
                first_name=first_name,
                verification_type=verification_type_display
            )
        else:
            return messages.format_message(
                messages.WELCOME_NO_CODE,
                first_name=first_name
            )
    
    @classmethod
    def format_phone_mismatch_message(
        cls,
        telegram_phone: str,
        registered_phone: str
    ) -> str:
        """Форматирует сообщение о несовпадении номеров телефона."""
        return messages.format_message(
            messages.ERROR_PHONE_MISMATCH,
            telegram_phone=cls.format_phone_display(telegram_phone),
            registered_phone=cls.format_phone_display(registered_phone)
        )
    
    @classmethod
    def format_registration_confirm_message(cls, phone: str) -> str:
        """Форматирует сообщение подтверждения регистрации."""
        return messages.format_message(
            messages.REGISTRATION_CONFIRM,
            phone=cls.format_phone_display(phone)
        )
    
    @classmethod
    def format_registration_success_message(cls, phone: str) -> str:
        """Форматирует сообщение об успешной регистрации."""
        return messages.format_message(
            messages.REGISTRATION_SUCCESS,
            phone=cls.format_phone_display(phone)
        )
    
    @classmethod
    def format_login_request_message(cls, phone: str) -> str:
        """Форматирует сообщение запроса на вход."""
        return messages.format_message(
            messages.LOGIN_REQUEST,
            phone=cls.format_phone_display(phone)
        )
    
    @classmethod
    def format_phone_change_request_message(cls, new_phone: str) -> str:
        """Форматирует сообщение запроса смены номера."""
        return messages.format_message(
            messages.PHONE_CHANGE_REQUEST,
            new_phone=cls.format_phone_display(new_phone)
        )
    
    @classmethod
    def format_rate_limit_message(cls, minutes: int) -> str:
        """Форматирует сообщение о превышении лимита."""
        return messages.format_message(
            messages.ERROR_RATE_LIMIT,
            minutes=minutes
        )


class PhoneFormatter:
    """Форматтер номеров телефонов."""
    
    @staticmethod
    def format_for_display(phone: str) -> str:
        """Форматирует номер для отображения пользователю."""
        return MessageFormatter.format_phone_display(phone)
    
    @staticmethod
    def format_for_storage(phone: str) -> str:
        """Форматирует номер для хранения в БД."""
        if not phone:
            return ""
        
        # Убираем все кроме цифр и +
        return re.sub(r'[^\d+]', '', phone)
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Маскирует номер телефона для логов."""
        if not phone or len(phone) < 4:
            return "***"
        
        return phone[:2] + "*" * (len(phone) - 4) + phone[-2:]