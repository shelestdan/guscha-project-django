#!/usr/bin/env python
"""
Тест для проверки полного потока входа по номеру телефона через Telegram бота.
Этот тест проверяет функциональность, которая была изменена в процессе оптимизации.
"""

import os
import sys
import django
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock
import asyncio
from asgiref.sync import sync_to_async

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guscha_django.settings.development')
django.setup()

from apps.accounts.models import TelegramVerificationCode
from apps.accounts.services.telegram_service import TelegramService
from telegram_bot.repositories.verification_code_repository import VerificationCodeRepository
from telegram_bot.services.verification_service import VerificationService

User = get_user_model()

class TelegramLoginFlowTest(TestCase):
    """Тест полного потока входа через Telegram бота."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.factory = RequestFactory()
        self.phone_number = '+1234567890'
        self.telegram_chat_id = '123456789'
        self.telegram_username = 'testuser'
        
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            phone=self.phone_number,
            email='testuser@example.com',
            telegram_chat_id=self.telegram_chat_id,
            telegram_username=self.telegram_username,
            is_active=True
        )
        
        # Инициализируем сервисы
        self.telegram_service = TelegramService()
        self.verification_repository = VerificationCodeRepository()
        self.verification_service = VerificationService()
    
    def cleanup_test_data(self):
        """Очистка тестовых данных."""
        try:
            TelegramVerificationCode.objects.filter(
                telegram_chat_id=self.telegram_chat_id
            ).delete()
            print("🧹 Тестовые данные очищены")
        except Exception as e:
            print(f"⚠️ Ошибка при очистке: {e}")
    
    def test_create_verification_code_sync(self):
        """Тест создания кода верификации (синхронный)."""
        print("\n=== Тест создания кода верификации (синхронный) ===")
        
        try:
            # Создаем код верификации через сервис
            result = self.telegram_service.create_verification_code(
                telegram_chat_id=self.telegram_chat_id,
                verification_type='login',
                user=self.user,
                telegram_phone=self.phone_number
            )
            
            print(f"✅ Код верификации создан: {result.id}")
            print(f"✅ Код для отображения: {result.generate_secure_code()}")
            
            # Проверяем, что код сохранен в базе данных
            verification_code = result
            
            self.assertEqual(verification_code.telegram_chat_id, int(self.telegram_chat_id))
            self.assertEqual(verification_code.verification_type, 'login')
            self.assertEqual(verification_code.user, self.user)
            
            print("✅ Синхронный тест создания кода верификации прошел успешно")
            return result
            
        except Exception as e:
            print(f"❌ Ошибка в синхронном тесте создания кода: {e}")
            raise
    
    async def test_create_verification_code_async(self):
        """Тест создания кода верификации (асинхронный)."""
        print("\n=== Тест создания кода верификации (асинхронный) ===")
        
        try:
            # Создаем код верификации через сервис (асинхронно)
            from django.contrib.auth import get_user_model
            from asgiref.sync import sync_to_async
            
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=self.user.id)
            
            verification_code = await sync_to_async(self.telegram_service.create_verification_code)(
                telegram_chat_id=self.telegram_chat_id,
                verification_type='login',
                user=user,
                telegram_phone=self.phone_number
            )
            
            print(f"✅ Асинхронный код верификации создан: {verification_code.id}")
            
            # Проверяем свойства кода
            self.assertEqual(verification_code.telegram_chat_id, int(self.telegram_chat_id))
            self.assertEqual(verification_code.verification_type, 'login')
            self.assertEqual(verification_code.user, user)
            
            print("✅ Асинхронный тест создания кода верификации прошел успешно")
            return verification_code
            
        except Exception as e:
            print(f"❌ Ошибка в асинхронном тесте создания кода: {e}")
            raise
    
    async def test_verify_code_async(self):
        """Тест верификации кода (асинхронный)."""
        print("\n=== Тест верификации кода (асинхронный) ===")
        
        try:
            from asgiref.sync import sync_to_async
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=self.user.id)
            
            # Сначала создаем код верификации через сервис
            verification_code = await sync_to_async(self.telegram_service.create_verification_code)(
                telegram_chat_id=self.telegram_chat_id,
                verification_type='login',
                user=user,
                telegram_phone=self.phone_number
            )
            
            # Получаем сгенерированный код
            display_code = await sync_to_async(verification_code.generate_secure_code)()
            print(f"✅ Код для верификации: {display_code}")
            
            # Проверяем код через сервис
            is_valid, _ = await sync_to_async(self.telegram_service.verify_code)(
                self.telegram_chat_id, display_code, 'login'
            )
            
            self.assertTrue(is_valid)
            print("✅ Асинхронный тест верификации кода прошел успешно")
            
        except Exception as e:
            print(f"❌ Ошибка в асинхронном тесте верификации кода: {e}")
            raise
    
    async def test_link_user_async(self):
        """Тест привязки пользователя к коду верификации (асинхронный)."""
        print("\n=== Тест привязки пользователя (асинхронный) ===")
        
        try:
            from asgiref.sync import sync_to_async
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            user = await sync_to_async(User.objects.get)(id=self.user.id)
            
            # Создаем код верификации напрямую через модель
            from apps.accounts.models import TelegramVerificationCode
            from django.utils import timezone
            from datetime import timedelta
            
            expires_at = timezone.now() + timedelta(minutes=10)
            verification_code = await TelegramVerificationCode.objects.acreate(
                verification_type='registration',
                telegram_chat_id=self.telegram_chat_id,
                telegram_phone=self.phone_number,
                expires_at=expires_at
            )
            
            # Сохраняем ID для последующего использования
            verification_code_id = verification_code.id
            
            # Привязываем пользователя через репозиторий
            await self.verification_repository.link_user(verification_code, user)
            
            # Получаем обновленный объект из базы данных
            verification_code = await self.verification_repository.get_by_id(str(verification_code_id))
            
            self.assertEqual(verification_code.user, user)
            print("✅ Асинхронный тест привязки пользователя прошел успешно")
            
        except Exception as e:
            print(f"❌ Ошибка в асинхронном тесте привязки пользователя: {e}")
            raise
    
    def test_full_login_flow(self):
        """Тест полного потока входа через Telegram."""
        print("\n=== Тест полного потока входа через Telegram ===")
        
        try:
            # 1. Инициация входа
            print("1. Инициация входа...")
            result = self.telegram_service.initiate_telegram_login(
                user=self.user,
                phone_number=self.phone_number
            )
            
            self.assertTrue(result['success'])
            display_code = result['verification_code']
            
            print(f"✅ Вход инициирован. Код: {display_code}")
            
            # 2. Получение кода верификации из базы данных
            print("2. Получение кода верификации...")
            verification_code = TelegramVerificationCode.objects.filter(
                user=self.user,
                verification_type='login',
                is_used=False
            ).first()
            
            # 3. Проверка кода
            print("3. Проверка кода...")
            is_valid = verification_code.check_code_match(display_code)
            self.assertTrue(is_valid)
            
            print("✅ Код верификации корректен")
            
            # 4. Верификация кода
            print("4. Верификация кода...")
            verify_result = verification_code.verify_code(display_code)
            self.assertTrue(verify_result)
            
            print("✅ Полный поток входа через Telegram прошел успешно")
            
        except Exception as e:
            print(f"❌ Ошибка в полном потоке входа: {e}")
            raise
    
    def run_async_tests(self):
        """Запуск асинхронных тестов."""
        print("\n=== Запуск асинхронных тестов ===")
        
        async def run_all_async():
            await self.test_create_verification_code_async()
            await sync_to_async(self.cleanup_test_data)()
            await self.test_verify_code_async()
            await sync_to_async(self.cleanup_test_data)()
            await self.test_link_user_async()
        
        # Запускаем асинхронные тесты
        asyncio.run(run_all_async())
        print("✅ Все асинхронные тесты завершены")

def main():
    """Главная функция для запуска тестов."""
    print("🚀 Запуск тестов входа через Telegram бота")
    print("=" * 60)
    
    # Создаем экземпляр теста
    test_case = TelegramLoginFlowTest()
    test_case.setUp()
    
    try:
        # Запускаем синхронные тесты
        print("\n📋 Синхронные тесты:")
        test_case.test_create_verification_code_sync()
        test_case.test_full_login_flow()
        
        # Запускаем асинхронные тесты
        print("\n📋 Асинхронные тесты:")
        test_case.run_async_tests()
        
        print("\n" + "=" * 60)
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Функция входа по номеру телефона через Telegram работает корректно")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ТЕСТЫ ПРОВАЛИЛИСЬ: {e}")
        print("🔧 Требуется исправление ошибок в коде")
        raise
    
    finally:
        # Очистка тестовых данных
        try:
            TelegramVerificationCode.objects.filter(
                telegram_chat_id=test_case.telegram_chat_id
            ).delete()
            test_case.user.delete()
            print("🧹 Тестовые данные очищены")
        except Exception as cleanup_error:
            print(f"⚠️ Ошибка при очистке: {cleanup_error}")

if __name__ == '__main__':
    main()