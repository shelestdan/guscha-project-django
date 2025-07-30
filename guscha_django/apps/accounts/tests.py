from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import PendingUserRegistration

User = get_user_model()


class UserRegistrationAPITest(APITestCase):
    """Тесты для API регистрации пользователей"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.registration_url = reverse('accounts:user-list')  # POST для создания пользователя
        self.valid_user_data = {
            'email': 'test@example.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь',
            'password': 'SecureP@ss9!',
            'password_confirm': 'SecureP@ss9!',
            'terms_accepted': True
        }
    
    def test_user_registration_success(self):
        """Тест успешной регистрации пользователя"""
        response = self.client.post(self.registration_url, self.valid_user_data, format='json')
        
        # Выводим ответ для отладки
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        # Проверяем, что запрос прошел успешно
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что создана pending регистрация
        self.assertTrue(
            PendingUserRegistration.objects.filter(
                email=self.valid_user_data['email']
            ).exists()
        )
        
        # Проверяем, что пользователь еще не создан в основной таблице
        self.assertFalse(
            User.objects.filter(
                email=self.valid_user_data['email']
            ).exists()
        )
    
    def test_user_registration_duplicate_email(self):
        """Тест регистрации с уже существующим email"""
        # Создаем пользователя
        User.objects.create_user(
            email=self.valid_user_data['email'],
            first_name='Существующий',
            last_name='Пользователь',
            password='password123'
        )
        
        response = self.client.post(self.registration_url, self.valid_user_data, format='json')
        
        # Проверяем, что запрос вернул ошибку
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['details'])
    
    def test_user_registration_invalid_data(self):
        """Тест регистрации с невалидными данными"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'  # Невалидный email
        
        response = self.client.post(self.registration_url, invalid_data, format='json')
        
        # Проверяем, что запрос вернул ошибку валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_registration_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPassword123!'
        
        response = self.client.post(self.registration_url, invalid_data, format='json')
        
        # Проверяем, что запрос вернул ошибку
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data['details'])


class PendingUserRegistrationModelTest(TestCase):
    """Тесты для модели PendingUserRegistration"""
    
    def test_pending_registration_creation(self):
        """Тест создания pending регистрации"""
        pending_reg = PendingUserRegistration.objects.create(
            email='test@example.com',
            first_name='Тест',
            last_name='Пользователь',
            password_hash='hashed_password'
        )
        
        # Проверяем, что объект создан
        self.assertTrue(pending_reg.id)
        self.assertEqual(pending_reg.email, 'test@example.com')
        self.assertIsNotNone(pending_reg.created_at)
        self.assertIsNotNone(pending_reg.expires_at)
        
        # Проверяем, что регистрация не истекла (только что создана)
        self.assertFalse(pending_reg.is_expired())
