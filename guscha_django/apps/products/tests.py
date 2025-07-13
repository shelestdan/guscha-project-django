from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from decimal import Decimal
import json

from .models import (
    Category, Product, ProductImage, ProductSize, 
    ProductVariant, ProductReview, Preorder, PreorderSize, Wishlist
)
from accounts.models import User


class CategoryModelTest(TestCase):
    """Тесты для модели Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category',
            description='Описание тестовой категории',
            is_active=True,
            sort_order=1
        )
        
        self.subcategory = Category.objects.create(
            name='Тестовая подкатегория',
            slug='test-subcategory',
            description='Описание тестовой подкатегории',
            parent=self.category,
            is_active=True,
            sort_order=1
        )
    
    def test_category_creation(self):
        """Тест создания категории"""
        self.assertEqual(self.category.name, 'Тестовая категория')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertEqual(self.category.description, 'Описание тестовой категории')
        self.assertTrue(self.category.is_active)
        self.assertEqual(self.category.sort_order, 1)
        self.assertIsNone(self.category.parent)
    
    def test_subcategory_creation(self):
        """Тест создания подкатегории"""
        self.assertEqual(self.subcategory.name, 'Тестовая подкатегория')
        self.assertEqual(self.subcategory.parent, self.category)
    
    def test_str_representation(self):
        """Тест строкового представления категории"""
        self.assertEqual(str(self.category), 'Тестовая категория')


class ProductModelTest(TestCase):
    """Тесты для модели Product"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            description='Описание тестового товара',
            short_description='Краткое описание',
            sku='TEST-SKU-001',
            category=self.category,
            price=Decimal('99.99'),
            compare_price=Decimal('129.99'),
            stock_quantity=10,
            is_active=True,
            is_featured=True
        )
        
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image_url='https://example.com/test-image.jpg',
            alt_text='Тестовое изображение',
            is_primary=True
        )
        
        self.product_size = ProductSize.objects.create(
            product=self.product,
            size_name='M',
            size_label='Средний',
            stock_quantity=5,
            is_active=True
        )
    
    def test_product_creation(self):
        """Тест создания товара"""
        self.assertEqual(self.product.name, 'Тестовый товар')
        self.assertEqual(self.product.slug, 'test-product')
        self.assertEqual(self.product.sku, 'TEST-SKU-001')
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(self.product.compare_price, Decimal('129.99'))
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertTrue(self.product.is_active)
        self.assertTrue(self.product.is_featured)
    
    def test_product_str_representation(self):
        """Тест строкового представления товара"""
        self.assertEqual(str(self.product), 'Тестовый товар')
    
    def test_product_primary_image(self):
        """Тест получения основного изображения товара"""
        self.assertEqual(self.product.primary_image(), self.product_image)
    
    def test_product_is_in_stock(self):
        """Тест проверки наличия товара на складе"""
        self.assertTrue(self.product.is_in_stock)
        
        # Установим количество в 0 и проверим, что товар не в наличии
        self.product.stock_quantity = 0
        self.product.save()
        self.assertFalse(self.product.is_in_stock)
    
    def test_product_available_sizes(self):
        """Тест получения доступных размеров товара"""
        available_sizes = self.product.available_sizes
        self.assertEqual(len(available_sizes), 1)
        self.assertEqual(available_sizes[0], self.product_size)
        
        # Создадим неактивный размер и проверим, что он не в списке доступных
        inactive_size = ProductSize.objects.create(
            product=self.product,
            size_name='L',
            size_label='Большой',
            stock_quantity=3,
            is_active=False
        )
        
        available_sizes = self.product.available_sizes
        self.assertEqual(len(available_sizes), 1)
        self.assertNotIn(inactive_size, available_sizes)


class ProductSizeModelTest(TestCase):
    """Тесты для модели ProductSize"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=10,
            is_active=True
        )
        
        self.product_size = ProductSize.objects.create(
            product=self.product,
            size_name='M',
            size_label='Средний',
            stock_quantity=5,
            is_active=True
        )
    
    def test_size_creation(self):
        """Тест создания размера товара"""
        self.assertEqual(self.product_size.product, self.product)
        self.assertEqual(self.product_size.size_name, 'M')
        self.assertEqual(self.product_size.size_label, 'Средний')
        self.assertEqual(self.product_size.stock_quantity, 5)
        self.assertTrue(self.product_size.is_active)
    
    def test_size_str_representation(self):
        """Тест строкового представления размера товара"""
        self.assertEqual(str(self.product_size), 'Тестовый товар - M')
    
    def test_size_is_available(self):
        """Тест проверки доступности размера"""
        self.assertTrue(self.product_size.is_available)
        
        # Проверим недоступность при неактивном размере
        self.product_size.is_active = False
        self.product_size.save()
        self.assertFalse(self.product_size.is_available)
        
        # Проверим недоступность при нулевом количестве
        self.product_size.is_active = True
        self.product_size.stock_quantity = 0
        self.product_size.save()
        self.assertFalse(self.product_size.is_available)


class ProductImageModelTest(TestCase):
    """Тесты для модели ProductImage"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image_url='https://example.com/test-image.jpg',
            alt_text='Тестовое изображение',
            sort_order=1,
            is_primary=True
        )
    
    def test_image_creation(self):
        """Тест создания изображения товара"""
        self.assertEqual(self.product_image.product, self.product)
        self.assertEqual(self.product_image.image_url, 'https://example.com/test-image.jpg')
        self.assertEqual(self.product_image.alt_text, 'Тестовое изображение')
        self.assertEqual(self.product_image.sort_order, 1)
        self.assertTrue(self.product_image.is_primary)
    
    def test_image_str_representation(self):
        """Тест строкового представления изображения товара"""
        self.assertEqual(str(self.product_image), 'Изображение для Тестовый товар')


class ProductVariantModelTest(TestCase):
    """Тесты для модели ProductVariant"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TEST-VAR-001',
            name='Тестовый вариант',
            price=Decimal('109.99'),
            stock_quantity=8,
            is_active=True,
            options=json.dumps({'color': 'Красный', 'material': 'Хлопок'})
        )
    
    def test_variant_creation(self):
        """Тест создания варианта товара"""
        self.assertEqual(self.variant.product, self.product)
        self.assertEqual(self.variant.sku, 'TEST-VAR-001')
        self.assertEqual(self.variant.name, 'Тестовый вариант')
        self.assertEqual(self.variant.price, Decimal('109.99'))
        self.assertEqual(self.variant.stock_quantity, 8)
        self.assertTrue(self.variant.is_active)
        
        # Проверим JSON-поле options
        options = json.loads(self.variant.options)
        self.assertEqual(options['color'], 'Красный')
        self.assertEqual(options['material'], 'Хлопок')
    
    def test_variant_str_representation(self):
        """Тест строкового представления варианта товара"""
        self.assertEqual(str(self.variant), 'Тестовый вариант')


class ProductReviewModelTest(TestCase):
    """Тесты для модели ProductReview"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            category=self.category,
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.review = ProductReview.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title='Отличный товар',
            content='Очень доволен покупкой, рекомендую!',
            verified_purchase=True,
            approved=True
        )
    
    def test_review_creation(self):
        """Тест создания отзыва на товар"""
        self.assertEqual(self.review.product, self.product)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.title, 'Отличный товар')
        self.assertEqual(self.review.content, 'Очень доволен покупкой, рекомендую!')
        self.assertTrue(self.review.verified_purchase)
        self.assertTrue(self.review.approved)
    
    def test_review_str_representation(self):
        """Тест строкового представления отзыва"""
        self.assertEqual(str(self.review), 'Отзыв на Тестовый товар от testuser')


class PreorderModelTest(TestCase):
    """Тесты для модели Preorder"""
    
    def setUp(self):
        self.preorder = Preorder.objects.create(
            name='Тестовый предзаказ',
            slug='test-preorder',
            description='Описание тестового предзаказа',
            price=Decimal('149.99'),
            compare_price=Decimal('199.99'),
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_active=True,
            is_recommended=True,
            meta_data=json.dumps({'collection': 'Весна 2023', 'designer': 'Тестовый дизайнер'})
        )
        
        self.preorder_size = PreorderSize.objects.create(
            preorder=self.preorder,
            size_name='M',
            size_label='Средний',
            max_quantity=10,
            is_active=True,
            is_sold_out=False,
            sort_order=1
        )
    
    def test_preorder_creation(self):
        """Тест создания предзаказа"""
        self.assertEqual(self.preorder.name, 'Тестовый предзаказ')
        self.assertEqual(self.preorder.slug, 'test-preorder')
        self.assertEqual(self.preorder.description, 'Описание тестового предзаказа')
        self.assertEqual(self.preorder.price, Decimal('149.99'))
        self.assertEqual(self.preorder.compare_price, Decimal('199.99'))
        self.assertTrue(self.preorder.is_active)
        self.assertTrue(self.preorder.is_recommended)
        
        # Проверим JSON-поле meta_data
        meta_data = json.loads(self.preorder.meta_data)
        self.assertEqual(meta_data['collection'], 'Весна 2023')
        self.assertEqual(meta_data['designer'], 'Тестовый дизайнер')
    
    def test_preorder_str_representation(self):
        """Тест строкового представления предзаказа"""
        self.assertEqual(str(self.preorder), 'Тестовый предзаказ')
    
    def test_preorder_is_active_now(self):
        """Тест проверки активности предзаказа по датам"""
        self.assertTrue(self.preorder.is_active_now)
        
        # Проверим неактивность при неактивном флаге
        self.preorder.is_active = False
        self.preorder.save()
        self.assertFalse(self.preorder.is_active_now)
        
        # Проверим неактивность при прошедшей дате окончания
        self.preorder.is_active = True
        self.preorder.end_date = timezone.now() - timezone.timedelta(days=1)
        self.preorder.save()
        self.assertFalse(self.preorder.is_active_now)
        
        # Проверим неактивность при будущей дате начала
        self.preorder.end_date = timezone.now() + timezone.timedelta(days=7)
        self.preorder.start_date = timezone.now() + timezone.timedelta(days=1)
        self.preorder.save()
        self.assertFalse(self.preorder.is_active_now)


class PreorderSizeModelTest(TestCase):
    """Тесты для модели PreorderSize"""
    
    def setUp(self):
        self.preorder = Preorder.objects.create(
            name='Тестовый предзаказ',
            slug='test-preorder',
            price=Decimal('149.99'),
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_active=True
        )
        
        self.preorder_size = PreorderSize.objects.create(
            preorder=self.preorder,
            size_name='M',
            size_label='Средний',
            max_quantity=10,
            is_active=True,
            is_sold_out=False,
            sort_order=1
        )
    
    def test_preorder_size_creation(self):
        """Тест создания размера предзаказа"""
        self.assertEqual(self.preorder_size.preorder, self.preorder)
        self.assertEqual(self.preorder_size.size_name, 'M')
        self.assertEqual(self.preorder_size.size_label, 'Средний')
        self.assertEqual(self.preorder_size.max_quantity, 10)
        self.assertTrue(self.preorder_size.is_active)
        self.assertFalse(self.preorder_size.is_sold_out)
        self.assertEqual(self.preorder_size.sort_order, 1)
    
    def test_preorder_size_str_representation(self):
        """Тест строкового представления размера предзаказа"""
        self.assertEqual(str(self.preorder_size), 'Тестовый предзаказ - M')
    
    def test_preorder_size_is_available(self):
        """Тест проверки доступности размера предзаказа"""
        self.assertTrue(self.preorder_size.is_available)
        
        # Проверим недоступность при неактивном размере
        self.preorder_size.is_active = False
        self.preorder_size.save()
        self.assertFalse(self.preorder_size.is_available)
        
        # Проверим недоступность при распроданном размере
        self.preorder_size.is_active = True
        self.preorder_size.is_sold_out = True
        self.preorder_size.save()
        self.assertFalse(self.preorder_size.is_available)
        
        # Проверим недоступность при неактивном предзаказе
        self.preorder_size.is_sold_out = False
        self.preorder.is_active = False
        self.preorder.save()
        self.assertFalse(self.preorder_size.is_available)


class CategoryAPITest(APITestCase):
    """Тесты для API категорий"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.category1 = Category.objects.create(
            name='Категория 1',
            slug='category-1',
            description='Описание категории 1',
            is_active=True,
            sort_order=1
        )
        
        self.category2 = Category.objects.create(
            name='Категория 2',
            slug='category-2',
            description='Описание категории 2',
            is_active=True,
            sort_order=2
        )
        
        self.subcategory = Category.objects.create(
            name='Подкатегория',
            slug='subcategory',
            description='Описание подкатегории',
            parent=self.category1,
            is_active=True,
            sort_order=1
        )
        
        # Создадим товары для категорий
        self.product1 = Product.objects.create(
            name='Товар 1',
            slug='product-1',
            category=self.category1,
            price=Decimal('99.99'),
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Товар 2',
            slug='product-2',
            category=self.category2,
            price=Decimal('149.99'),
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            name='Товар 3',
            slug='product-3',
            category=self.subcategory,
            price=Decimal('199.99'),
            is_active=True
        )
    
    def test_category_list(self):
        """Тест получения списка категорий"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Только родительские категории
        
        # Проверим, что в ответе есть нужные поля
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])
        self.assertIn('slug', response.data[0])
        self.assertIn('description', response.data[0])
        self.assertIn('product_count', response.data[0])
        
        # Проверим, что категории отсортированы по sort_order
        self.assertEqual(response.data[0]['name'], 'Категория 1')
        self.assertEqual(response.data[1]['name'], 'Категория 2')
    
    def test_category_detail(self):
        """Тест получения детальной информации о категории"""
        url = reverse('category-detail', kwargs={'slug': self.category1.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Категория 1')
        self.assertEqual(response.data['slug'], 'category-1')
        
        # Проверим, что в ответе есть подкатегории
        self.assertIn('subcategories', response.data)
        self.assertEqual(len(response.data['subcategories']), 1)
        self.assertEqual(response.data['subcategories'][0]['name'], 'Подкатегория')
    
    def test_category_products(self):
        """Тест получения товаров категории"""
        url = reverse('category-products', kwargs={'slug': self.category1.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только товары непосредственно в категории
        self.assertEqual(response.data[0]['name'], 'Товар 1')


class ProductAPITest(APITestCase):
    """Тесты для API товаров"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создадим пользователя для тестирования
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создадим администратора для тестирования
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Тестовый товар',
            slug='test-product',
            description='Описание тестового товара',
            short_description='Краткое описание',
            sku='TEST-SKU-001',
            category=self.category,
            price=Decimal('99.99'),
            compare_price=Decimal('129.99'),
            stock_quantity=10,
            is_active=True,
            is_featured=True
        )
        
        self.product_image = ProductImage.objects.create(
            product=self.product,
            image_url='https://example.com/test-image.jpg',
            alt_text='Тестовое изображение',
            is_primary=True
        )
        
        self.product_size = ProductSize.objects.create(
            product=self.product,
            size_name='M',
            size_label='Средний',
            stock_quantity=5,
            is_active=True
        )
    
    def test_product_list(self):
        """Тест получения списка товаров"""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Проверим, что в ответе есть нужные поля
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])
        self.assertIn('slug', response.data[0])
        self.assertIn('price', response.data[0])
        self.assertIn('category_name', response.data[0])
        self.assertIn('primary_image', response.data[0])
    
    def test_product_detail(self):
        """Тест получения детальной информации о товаре"""
        url = reverse('product-detail', kwargs={'slug': self.product.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Тестовый товар')
        self.assertEqual(response.data['slug'], 'test-product')
        self.assertEqual(response.data['price'], '99.99')
        
        # Проверим, что в ответе есть изображения, размеры и другие связанные данные
        self.assertIn('images', response.data)
        self.assertEqual(len(response.data['images']), 1)
        
        self.assertIn('sizes', response.data)
        self.assertEqual(len(response.data['sizes']), 1)
        self.assertEqual(response.data['sizes'][0]['size_name'], 'M')
    
    def test_product_create(self):
        """Тест создания товара (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('product-list')
        data = {
            'name': 'Новый товар',
            'description': 'Описание нового товара',
            'short_description': 'Краткое описание',
            'sku': 'NEW-SKU-001',
            'category': self.category.id,
            'price': '199.99',
            'compare_price': '249.99',
            'stock_quantity': 20,
            'is_active': True,
            'is_featured': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Новый товар')
        self.assertEqual(response.data['price'], '199.99')
        
        # Проверим, что товар действительно создан в базе
        self.assertTrue(Product.objects.filter(name='Новый товар').exists())
    
    def test_product_update(self):
        """Тест обновления товара (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('product-detail', kwargs={'slug': self.product.slug})
        data = {
            'name': 'Обновленный товар',
            'price': '129.99'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Обновленный товар')
        self.assertEqual(response.data['price'], '129.99')
        
        # Проверим, что товар действительно обновлен в базе
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Обновленный товар')
        self.assertEqual(self.product.price, Decimal('129.99'))
    
    def test_product_delete(self):
        """Тест удаления товара (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('product-detail', kwargs={'slug': self.product.slug})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверим, что товар действительно удален из базы
        self.assertFalse(Product.objects.filter(slug=self.product.slug).exists())
    
    def test_product_review_create(self):
        """Тест создания отзыва на товар (только для авторизованных пользователей)"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('product-reviews-list', kwargs={'product_slug': self.product.slug})
        data = {
            'rating': 5,
            'title': 'Отличный товар',
            'content': 'Очень доволен покупкой, рекомендую!'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['title'], 'Отличный товар')
        
        # Проверим, что отзыв действительно создан в базе
        self.assertTrue(ProductReview.objects.filter(user=self.user, product=self.product).exists())


class PreorderAPITest(APITestCase):
    """Тесты для API предзаказов"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создадим пользователя для тестирования
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создадим администратора для тестирования
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.preorder = Preorder.objects.create(
            name='Тестовый предзаказ',
            slug='test-preorder',
            description='Описание тестового предзаказа',
            price=Decimal('149.99'),
            compare_price=Decimal('199.99'),
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_active=True,
            is_recommended=True,
            meta_data=json.dumps({'collection': 'Весна 2023', 'designer': 'Тестовый дизайнер'})
        )
        
        self.preorder_size = PreorderSize.objects.create(
            preorder=self.preorder,
            size_name='M',
            size_label='Средний',
            max_quantity=10,
            is_active=True,
            is_sold_out=False,
            sort_order=1
        )
        
        # Создадим неактивный предзаказ
        self.inactive_preorder = Preorder.objects.create(
            name='Неактивный предзаказ',
            slug='inactive-preorder',
            description='Описание неактивного предзаказа',
            price=Decimal('129.99'),
            start_date=timezone.now() - timezone.timedelta(days=10),
            end_date=timezone.now() - timezone.timedelta(days=3),  # Уже закончился
            is_active=True
        )
    
    def test_preorder_list(self):
        """Тест получения списка активных предзаказов"""
        url = reverse('preorder-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только активные предзаказы
        
        # Проверим, что в ответе есть нужные поля
        self.assertIn('id', response.data[0])
        self.assertIn('name', response.data[0])
        self.assertIn('slug', response.data[0])
        self.assertIn('price', response.data[0])
        self.assertIn('compare_price', response.data[0])
        self.assertIn('start_date', response.data[0])
        self.assertIn('end_date', response.data[0])
    
    def test_preorder_detail(self):
        """Тест получения детальной информации о предзаказе"""
        url = reverse('preorder-detail', kwargs={'slug': self.preorder.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Тестовый предзаказ')
        self.assertEqual(response.data['slug'], 'test-preorder')
        self.assertEqual(response.data['price'], '149.99')
        
        # Проверим, что в ответе есть размеры и метаданные
        self.assertIn('sizes', response.data)
        self.assertEqual(len(response.data['sizes']), 1)
        self.assertEqual(response.data['sizes'][0]['size_name'], 'M')
        
        self.assertIn('meta_data', response.data)
        meta_data = json.loads(response.data['meta_data'])
        self.assertEqual(meta_data['collection'], 'Весна 2023')
    
    def test_inactive_preorder_detail(self):
        """Тест получения детальной информации о неактивном предзаказе"""
        url = reverse('preorder-detail', kwargs={'slug': self.inactive_preorder.slug})
        response = self.client.get(url)
        
        # Должен вернуть 404, так как предзаказ неактивен (закончился)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_preorder_create(self):
        """Тест создания предзаказа (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('preorder-list')
        data = {
            'name': 'Новый предзаказ',
            'description': 'Описание нового предзаказа',
            'price': '179.99',
            'compare_price': '229.99',
            'start_date': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'end_date': (timezone.now() + timezone.timedelta(days=14)).isoformat(),
            'is_active': True,
            'is_recommended': True,
            'meta_data': json.dumps({'collection': 'Лето 2023', 'designer': 'Новый дизайнер'})
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Новый предзаказ')
        self.assertEqual(response.data['price'], '179.99')
        
        # Проверим, что предзаказ действительно создан в базе
        self.assertTrue(Preorder.objects.filter(name='Новый предзаказ').exists())
    
    def test_preorder_update(self):
        """Тест обновления предзаказа (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('preorder-detail', kwargs={'slug': self.preorder.slug})
        data = {
            'name': 'Обновленный предзаказ',
            'price': '159.99'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Обновленный предзаказ')
        self.assertEqual(response.data['price'], '159.99')
        
        # Проверим, что предзаказ действительно обновлен в базе
        self.preorder.refresh_from_db()
        self.assertEqual(self.preorder.name, 'Обновленный предзаказ')
        self.assertEqual(self.preorder.price, Decimal('159.99'))
    
    def test_preorder_delete(self):
        """Тест удаления предзаказа (только для администраторов)"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('preorder-detail', kwargs={'slug': self.preorder.slug})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверим, что предзаказ действительно удален из базы
        self.assertFalse(Preorder.objects.filter(slug=self.preorder.slug).exists())


class WishlistAPITest(APITestCase):
    """Тесты для API списка желаний"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Создадим пользователя для тестирования
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Создадим категорию для тестирования
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category',
            description='Описание тестовой категории',
            is_active=True
        )
        
        # Создадим продукты для тестирования
        self.product1 = Product.objects.create(
            name='Тестовый продукт 1',
            slug='test-product-1',
            description='Описание тестового продукта 1',
            price=Decimal('99.99'),
            category=self.category,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Тестовый продукт 2',
            slug='test-product-2',
            description='Описание тестового продукта 2',
            price=Decimal('149.99'),
            category=self.category,
            is_active=True
        )
        
        # Создадим элемент списка желаний
        self.wishlist_item = Wishlist.objects.create(
            user=self.user,
            product=self.product1
        )
    
    def test_wishlist_list_unauthorized(self):
        """Тест получения списка желаний без авторизации"""
        url = reverse('wishlist-list')
        response = self.client.get(url)
        
        # Должен вернуть 401, так как пользователь не авторизован
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_wishlist_list_authorized(self):
        """Тест получения списка желаний с авторизацией"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('wishlist-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Один элемент в списке желаний
        
        # Проверим, что в ответе есть нужные поля
        self.assertIn('id', response.data[0])
        self.assertIn('product', response.data[0])
        self.assertEqual(response.data[0]['product']['id'], self.product1.id)
        self.assertEqual(response.data[0]['product']['name'], 'Тестовый продукт 1')
    
    def test_add_to_wishlist(self):
        """Тест добавления продукта в список желаний"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('wishlist-list')
        data = {
            'product_id': self.product2.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product']['id'], self.product2.id)
        
        # Проверим, что элемент действительно добавлен в базу
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product2).exists())
    
    def test_add_duplicate_to_wishlist(self):
        """Тест добавления дубликата продукта в список желаний"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('wishlist-list')
        data = {
            'product_id': self.product1.id  # Этот продукт уже в списке желаний
        }
        
        response = self.client.post(url, data, format='json')
        
        # Должен вернуть ошибку, так как продукт уже в списке желаний
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_remove_from_wishlist(self):
        """Тест удаления продукта из списка желаний"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('wishlist-detail', kwargs={'pk': self.wishlist_item.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Проверим, что элемент действительно удален из базы
        self.assertFalse(Wishlist.objects.filter(id=self.wishlist_item.id).exists())
    
    def test_check_product_in_wishlist(self):
        """Тест проверки наличия продукта в списке желаний"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('product-detail', kwargs={'slug': self.product1.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('in_wishlist', response.data)
        self.assertTrue(response.data['in_wishlist'])  # Продукт должен быть в списке желаний
        
        # Проверим продукт, которого нет в списке желаний
        url = reverse('product-detail', kwargs={'slug': self.product2.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('in_wishlist', response.data)
        self.assertFalse(response.data['in_wishlist'])  # Продукт не должен быть в списке желаний
