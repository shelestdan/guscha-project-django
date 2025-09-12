"""Тесты безопасности для Telegram валидатора."""

import unittest
import time
import logging
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.validators.telegram_validator import TelegramValidator


class TelegramSecurityTestCase(TestCase):
    """Тесты безопасности для TelegramValidator."""
    
    def setUp(self):
        """Настройка тестов."""
        self.validator = TelegramValidator()
        
        # Настройка логгеров для тестирования
        self.security_logger = logging.getLogger('security.telegram')
        self.suspicious_logger = logging.getLogger('security.telegram.suspicious')
        
        # Создаем mock handlers для проверки логирования
        self.security_handler = MagicMock()
        self.suspicious_handler = MagicMock()
        
        # Настраиваем уровни для mock handlers
        self.security_handler.level = logging.INFO
        self.suspicious_handler.level = logging.WARNING
        
        self.security_logger.addHandler(self.security_handler)
        self.suspicious_logger.addHandler(self.suspicious_handler)
        
        self.security_logger.setLevel(logging.INFO)
        self.suspicious_logger.setLevel(logging.WARNING)
        
        # Патчим логгеры в валидаторе для тестирования
        self.validator.logger = self.security_logger
        self.validator.suspicious_logger = self.suspicious_logger
    
    def tearDown(self):
        """Очистка после тестов."""
        self.security_logger.removeHandler(self.security_handler)
        self.suspicious_logger.removeHandler(self.suspicious_handler)
    
    def test_secure_code_compare_timing_attack_protection(self):
        """Тест защиты от timing атак в secure_code_compare."""
        correct_code = "123456"
        wrong_code = "654321"
        
        # Измеряем время выполнения для правильного кода
        start_time = time.perf_counter()
        result_correct = self.validator.secure_code_compare(correct_code, correct_code)
        correct_time = time.perf_counter() - start_time
        
        # Измеряем время выполнения для неправильного кода
        start_time = time.perf_counter()
        result_wrong = self.validator.secure_code_compare(wrong_code, correct_code)
        wrong_time = time.perf_counter() - start_time
        
        # Проверяем результаты
        self.assertTrue(result_correct)
        self.assertFalse(result_wrong)
        
        # Проверяем, что разница во времени минимальна (защита от timing атак)
        time_difference = abs(correct_time - wrong_time)
        self.assertLess(time_difference, 0.001, "Timing attack protection failed")
    
    def test_secure_code_compare_with_different_lengths(self):
        """Тест secure_code_compare с кодами разной длины."""
        short_code = "123"
        long_code = "123456789"
        
        # Тест с кодами разной длины
        result = self.validator.secure_code_compare(short_code, long_code)
        self.assertFalse(result)
        
        # Проверяем логирование
        self.security_handler.handle.assert_called()
    
    def test_secure_code_compare_with_non_string_input(self):
        """Тест secure_code_compare с не-строковыми входными данными."""
        # Тест с числом
        result = self.validator.secure_code_compare(123456, "123456")
        self.assertFalse(result)
        
        # Тест с None
        result = self.validator.secure_code_compare(None, "123456")
        self.assertFalse(result)
        
        # Проверяем логирование подозрительной активности
        self.suspicious_handler.handle.assert_called()
    
    def test_sanitize_telegram_input_xss_protection(self):
        """Тест защиты от XSS в sanitize_telegram_input."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "&lt;script&gt;alert('xss')&lt;/script&gt;"
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = self.validator.sanitize_telegram_input(malicious_input)
            
            # Проверяем, что опасные символы удалены
            self.assertNotIn('<', sanitized)
            self.assertNotIn('>', sanitized)
            self.assertNotIn('script', sanitized.lower())
            self.assertNotIn('javascript:', sanitized.lower())
    
    def test_sanitize_telegram_input_sql_injection_protection(self):
        """Тест защиты от SQL инъекций в sanitize_telegram_input."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "UNION SELECT * FROM users",
            "'; DELETE FROM accounts; --",
            "' OR 1=1 --"
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = self.validator.sanitize_telegram_input(malicious_input)
            
            # Проверяем, что опасные SQL конструкции удалены
            self.assertNotIn(';', sanitized)
            self.assertNotIn('--', sanitized)
            self.assertNotIn('DROP', sanitized.upper())
            self.assertNotIn('DELETE', sanitized.upper())
            self.assertNotIn('UNION', sanitized.upper())
    
    def test_sanitize_telegram_input_length_limit(self):
        """Тест ограничения длины в sanitize_telegram_input."""
        # Создаем очень длинную строку
        long_input = "A" * 2000
        
        sanitized = self.validator.sanitize_telegram_input(long_input)
        
        # Проверяем, что длина ограничена
        self.assertLessEqual(len(sanitized), self.validator.MAX_INPUT_LENGTH)
    
    def test_sanitize_telegram_input_whitespace_handling(self):
        """Тест обработки пробелов в sanitize_telegram_input."""
        inputs_with_whitespace = [
            "  test  ",
            "\n\ttest\r\n",
            "   multiple   spaces   ",
            "\x00null\x00bytes\x00"
        ]
        
        for input_data in inputs_with_whitespace:
            sanitized = self.validator.sanitize_telegram_input(input_data)
            
            # Проверяем, что пробелы обрезаны
            self.assertEqual(sanitized, sanitized.strip())
            # Проверяем, что null-байты удалены
            self.assertNotIn('\x00', sanitized)
    
    def test_verification_code_validation_logging(self):
        """Тест логирования при валидации кода верификации."""
        user_id = 123
        chat_id = 456789
        
        # Тест успешной валидации
        try:
            self.validator.validate_verification_code("123456", user_id=user_id, chat_id=chat_id)
        except ValidationError:
            pass  # Ожидаем ValidationError, но нас интересует логирование
        
        # Проверяем, что логирование произошло
        self.security_handler.handle.assert_called()
        
        # Тест с пустым кодом (подозрительная активность)
        try:
            self.validator.validate_verification_code("", user_id=user_id, chat_id=chat_id)
        except ValidationError:
            pass
        
        # Проверяем логирование подозрительной активности
        self.suspicious_handler.handle.assert_called()
    
    def test_verification_code_validation_oversized_input(self):
        """Тест валидации кода верификации с превышением размера."""
        user_id = 123
        chat_id = 456789
        oversized_code = "A" * 50  # Превышает MAX_CODE_LENGTH
        
        try:
            self.validator.validate_verification_code(oversized_code, user_id=user_id, chat_id=chat_id)
        except ValidationError:
            pass
        
        # Проверяем логирование подозрительной активности
        self.suspicious_handler.handle.assert_called()
    
    def test_verification_code_validation_invalid_characters(self):
        """Тест валидации кода верификации с недопустимыми символами."""
        user_id = 123
        chat_id = 456789
        invalid_codes = [
            "123!@#",
            "код123",
            "123<script>",
            "123'; DROP"
        ]
        
        for invalid_code in invalid_codes:
            try:
                self.validator.validate_verification_code(invalid_code, user_id=user_id, chat_id=chat_id)
            except ValidationError:
                pass
            
            # Проверяем логирование подозрительной активности
            self.suspicious_handler.handle.assert_called()
    
    def test_security_logging_integration(self):
        """Тест интеграции системы логирования безопасности."""
        user_id = 999
        chat_id = 888777
        
        # Тест различных подозрительных активностей
        suspicious_activities = [
            ("validate_verification_code", ["", user_id, chat_id]),
            ("validate_verification_code", [None, user_id, chat_id]),
            ("secure_code_compare", [123, "456", user_id, chat_id]),
            ("secure_code_compare", ["123", None, user_id, chat_id])
        ]
        
        for method_name, args in suspicious_activities:
            try:
                method = getattr(self.validator, method_name)
                method(*args)
            except (ValidationError, TypeError, AttributeError):
                pass  # Ожидаем ошибки, но нас интересует логирование
        
        # Проверяем, что все подозрительные активности залогированы
        self.assertGreater(self.suspicious_handler.handle.call_count, 0)
    
    def test_constant_time_comparison_consistency(self):
        """Тест консистентности constant-time сравнения."""
        test_cases = [
            ("123456", "123456", True),
            ("123456", "654321", False),
            ("abc123", "abc123", True),
            ("abc123", "xyz789", False),
            ("", "", True),
            ("a", "b", False)
        ]
        
        for code1, code2, expected in test_cases:
            result = self.validator.secure_code_compare(code1, code2)
            self.assertEqual(result, expected, 
                           f"Failed for codes: '{code1}' vs '{code2}'")
    
    def test_input_sanitization_edge_cases(self):
        """Тест граничных случаев санитизации входных данных."""
        edge_cases = [
            "",  # Пустая строка
            " ",  # Только пробел
            "\n\r\t",  # Только whitespace символы
            "\x00\x01\x02",  # Control символы
            "🚀💻🔒",  # Unicode emoji
            "тест",  # Кириллица
            "测试",  # Китайские символы
        ]
        
        for edge_case in edge_cases:
            sanitized = self.validator.sanitize_telegram_input(edge_case)
            
            # Проверяем, что результат всегда строка
            self.assertIsInstance(sanitized, str)
            
            # Проверяем, что длина не превышает лимит
            self.assertLessEqual(len(sanitized), self.validator.MAX_INPUT_LENGTH)


if __name__ == '__main__':
    unittest.main()