from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Address

User = get_user_model()


class AddressModelTest(TestCase):
    """Тесты модели Address"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_address(self):
        """Тест создания адреса"""
        address = Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Иван',
            last_name='Иванов',
            address_line1='ул. Ленина, д. 1',
            city='Москва',
            postal_code='123456',
            country='Russia',
            phone='+7 (999) 123-45-67',
            is_default=True
        )
        
        self.assertEqual(str(address), 'Иван Иванов, ул. Ленина, д. 1, Москва')
        self.assertEqual(address.full_name, 'Иван Иванов')
        self.assertIn('ул. Ленина, д. 1', address.full_address)
    
    def test_default_address_uniqueness(self):
        """Тест уникальности адреса по умолчанию"""
        # Создаем первый адрес по умолчанию
        Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Иван',
            last_name='Иванов',
            address_line1='ул. Ленина, д. 1',
            city='Москва',
            postal_code='123456',
            country='Russia',
            is_default=True
        )
        
        # Создаем второй адрес и устанавливаем его по умолчанию
        address2 = Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Петр',
            last_name='Петров',
            address_line1='ул. Пушкина, д. 2',
            city='Москва',
            postal_code='123457',
            country='Russia',
            is_default=True
        )
        
        # Проверяем, что первый адрес больше не по умолчанию
        first_address = Address.objects.get(first_name='Иван')
        self.assertFalse(first_address.is_default)
        self.assertTrue(address2.is_default)
    
    def test_soft_delete(self):
        """Тест мягкого удаления"""
        address = Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Иван',
            last_name='Иванов',
            address_line1='ул. Ленина, д. 1',
            city='Москва',
            postal_code='123456',
            country='Russia'
        )
        
        # Мягкое удаление
        address.is_active = False
        address.save()
        
        # Адрес должен быть скрыт из активных
        active_addresses = Address.objects.filter(is_active=True)
        self.assertEqual(active_addresses.count(), 0)
        
        # Но все еще существует в базе
        all_addresses = Address.objects.all()
        self.assertEqual(all_addresses.count(), 1)


class AddressAPITest(APITestCase):
    """Тесты API адресов"""
    
    def setUp(self):
        # Очищаем все адреса перед каждым тестом
        Address.objects.all().delete()
        
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.address_data = {
            'address_type': 'shipping',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'address_line1': 'ул. Ленина, д. 1',
            'city': 'Москва',
            'postal_code': '123456',
            'country': 'Russia',
            'phone': '+7 (999) 123-45-67',
            'is_default': True
        }
    
    def test_create_address_api(self):
        """Тест создания адреса через API"""
        url = reverse('address-list')
        response = self.client.post(url, self.address_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(Address.objects.get().first_name, 'Иван')
    
    def test_list_addresses_api(self):
        """Тест получения списка адресов"""
        Address.objects.create(user=self.user, **self.address_data)
        
        url = reverse('address-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_update_address_api(self):
        """Тест обновления адреса"""
        address = Address.objects.create(user=self.user, **self.address_data)
        
        url = reverse('address-detail', kwargs={'pk': address.id})
        updated_data = self.address_data.copy()
        updated_data['first_name'] = 'Петр'
        
        response = self.client.put(url, updated_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        address.refresh_from_db()
        self.assertEqual(address.first_name, 'Петр')
    
    def test_delete_address_api(self):
        """Тест удаления адреса (soft delete)"""
        address = Address.objects.create(user=self.user, **self.address_data)
        
        url = reverse('address-detail', kwargs={'pk': address.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        address.refresh_from_db()
        self.assertFalse(address.is_active)
    
    def test_set_default_address_api(self):
        """Тест установки адреса по умолчанию"""
        address1 = Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Иван',
            last_name='Иванов',
            address_line1='ул. Ленина, д. 1',
            city='Москва',
            postal_code='123456',
            country='Russia',
            is_default=True
        )
        
        address2 = Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Петр',
            last_name='Петров',
            address_line1='ул. Пушкина, д. 2',
            city='Москва',
            postal_code='123457',
            country='Russia',
            is_default=False
        )
        
        url = reverse('address-set-default', kwargs={'pk': address2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        address1.refresh_from_db()
        address2.refresh_from_db()
        
        self.assertFalse(address1.is_default)
        self.assertTrue(address2.is_default)
    
    def test_user_can_only_see_own_addresses(self):
        """Тест, что пользователь видит только свои адреса"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        Address.objects.create(
            user=other_user,
            address_type='shipping',
            first_name='Другой',
            last_name='Пользователь',
            address_line1='ул. Другая, д. 1',
            city='Москва',
            postal_code='123458',
            country='Russia'
        )
        
        Address.objects.create(
            user=self.user,
            address_type='shipping',
            first_name='Мой',
            last_name='Адрес',
            address_line1='ул. Моя, д. 1',
            city='Москва',
            postal_code='123459',
            country='Russia'
        )
        
        url = reverse('address-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'Мой')


class AddressValidationTest(APITestCase):
    """Тесты валидации адресов"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_required_fields(self):
        """Тест обязательных полей"""
        url = reverse('address-list')
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('address_line1', response.data)
        self.assertIn('city', response.data)
        self.assertIn('postal_code', response.data)