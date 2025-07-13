from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Order, OrderItem
from apps.products.models import Product, Category

User = get_user_model()


class OrderModelTest(TestCase):
    """
    Тесты модели Order
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100.00,
            stock=10,
            category=self.category
        )
    
    def test_order_creation(self):
        """Тест создания заказа"""
        order = Order.objects.create(
            user=self.user,
            status='pending'
        )
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total_amount, 0)
        self.assertEqual(order.total_quantity, 0)
    
    def test_order_totals_calculation(self):
        """Тест расчета общих сумм заказа"""
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price=100.00
        )
        
        order.update_totals()
        self.assertEqual(order.total_amount, 200.00)
        self.assertEqual(order.total_quantity, 2)
    
    def test_order_str_method(self):
        """Тест строкового представления заказа"""
        order = Order.objects.create(user=self.user)
        expected_str = f"Заказ #{order.id} - {self.user.email}"
        self.assertEqual(str(order), expected_str)


class OrderItemModelTest(TestCase):
    """
    Тесты модели OrderItem
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100.00,
            stock=10,
            category=self.category
        )
        self.order = Order.objects.create(user=self.user)
    
    def test_order_item_creation(self):
        """Тест создания элемента заказа"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=100.00
        )
        self.assertEqual(item.total_price, 200.00)
        self.assertEqual(item.order.total_amount, 200.00)
    
    def test_order_item_str_method(self):
        """Тест строкового представления элемента заказа"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=100.00
        )
        expected_str = f"{self.product.name} x 1 в заказе #{self.order.id}"
        self.assertEqual(str(item), expected_str)


class OrderAPITest(APITestCase):
    """
    Тесты API заказов
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100.00,
            stock=10,
            category=self.category
        )
        self.order = Order.objects.create(user=self.user)
    
    def test_create_order_authenticated(self):
        """Тест создания заказа аутентифицированным пользователем"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_order_unauthenticated(self):
        """Тест создания заказа неаутентифицированным пользователем"""
        url = reverse('order-list')
        data = {
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_user_orders(self):
        """Тест получения списка заказов пользователя"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_admin_can_see_all_orders(self):
        """Тест что админ видит все заказы"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_cannot_see_others_orders(self):
        """Тест что пользователь не видит чужие заказы"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        Order.objects.create(user=other_user)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)  # Только свой заказ
    
    def test_order_status_change(self):
        """Тест изменения статуса заказа"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('order-confirm', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
    
    def test_user_cannot_change_status(self):
        """Тест что обычный пользователь не может менять статус"""
        self.client.force_authenticate(user=self.user)
        url = reverse('order-confirm', kwargs={'pk': self.order.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_filtering(self):
        """Тест фильтрации заказов"""
        self.client.force_authenticate(user=self.user)
        
        # Создаем заказ с другим статусом
        Order.objects.create(user=self.user, status='confirmed')
        
        url = reverse('order-list')
        response = self.client.get(url, {'status': 'pending'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
