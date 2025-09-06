from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category
from apps.background_content.models import BackgroundContent
from apps.orders.models import Order
from decimal import Decimal
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Восстанавливает базовые данные для сайта'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@guscha.ru',
            help='Email для администратора'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='Пароль для администратора'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаю восстановление данных...'))
        
        # Создаем администратора
        admin_email = options['admin_email']
        admin_password = options['admin_password']
        
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name='Администратор',
                last_name='Сайта'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Создан администратор: {admin_email}')
            )
        else:
            admin_user = User.objects.get(email=admin_email)
            self.stdout.write(
                self.style.WARNING(f'Администратор уже существует: {admin_email}')
            )

        # Создаем тестовых пользователей
        test_users = [
            {
                'email': 'user1@test.ru',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'password': 'testpass123'
            },
            {
                'email': 'user2@test.ru', 
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'password': 'testpass123'
            }
        ]
        
        for user_data in test_users:
            if not User.objects.filter(email=user_data['email']).exists():
                User.objects.create_user(
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Создан пользователь: {user_data["email"]}')
                )

        # Создаем категории
        categories_data = [
            {'name': 'Электроника', 'slug': 'electronics'},
            {'name': 'Одежда', 'slug': 'clothing'},
            {'name': 'Книги', 'slug': 'books'},
            {'name': 'Дом и сад', 'slug': 'home-garden'},
            {'name': 'Спорт', 'slug': 'sport'}
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name']}
            )
            created_categories.append(category)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создана категория: {category.name}')
                )

        # Создаем товары
        products_data = [
            {
                'name': 'iPhone 15 Pro',
                'slug': 'iphone-15-pro',
                'sku': 'IPHONE-15-PRO-001',
                'description': 'Новейший смартфон Apple с передовыми технологиями',
                'price': Decimal('89999.00'),
                'stock_quantity': 10,
                'category': created_categories[0],  # Электроника
                'is_active': True
            },
            {
                'name': 'Samsung Galaxy S24',
                'slug': 'samsung-galaxy-s24',
                'sku': 'SAMSUNG-S24-002',
                'description': 'Флагманский смартфон Samsung с AI функциями',
                'price': Decimal('79999.00'),
                'stock_quantity': 15,
                'category': created_categories[0],  # Электроника
                'is_active': True
            },
            {
                'name': 'Куртка зимняя',
                'slug': 'winter-jacket',
                'sku': 'JACKET-WINTER-003',
                'description': 'Теплая зимняя куртка для холодной погоды',
                'price': Decimal('5999.00'),
                'stock_quantity': 25,
                'category': created_categories[1],  # Одежда
                'is_active': True
            },
            {
                'name': 'Джинсы классические',
                'slug': 'classic-jeans',
                'sku': 'JEANS-CLASSIC-004',
                'description': 'Классические джинсы из качественного денима',
                'price': Decimal('3499.00'),
                'stock_quantity': 30,
                'category': created_categories[1],  # Одежда
                'is_active': True
            },
            {
                'name': 'Программирование на Python',
                'slug': 'python-programming-book',
                'sku': 'BOOK-PYTHON-005',
                'description': 'Полное руководство по программированию на Python',
                'price': Decimal('1299.00'),
                'stock_quantity': 50,
                'category': created_categories[2],  # Книги
                'is_active': True
            },
            {
                'name': 'Кофеварка автоматическая',
                'slug': 'automatic-coffee-maker',
                'sku': 'COFFEE-AUTO-006',
                'description': 'Автоматическая кофеварка для дома и офиса',
                'price': Decimal('12999.00'),
                'stock_quantity': 8,
                'category': created_categories[3],  # Дом и сад
                'is_active': True
            },
            {
                'name': 'Беговые кроссовки',
                'slug': 'running-sneakers',
                'sku': 'SNEAKERS-RUN-007',
                'description': 'Профессиональные беговые кроссовки для спорта',
                'price': Decimal('7999.00'),
                'stock_quantity': 20,
                'category': created_categories[4],  # Спорт
                'is_active': True
            }
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults=product_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создан товар: {product.name}')
                )

        # Создаем фоновый контент
        self.stdout.write('Создание фонового контента...')
        bg_content, created = BackgroundContent.objects.get_or_create(
            title='Главный фон сайта',
            defaults={
                'content_type': 'image',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Фоновый контент создан'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Фоновый контент уже существует'))

        # Создаем тестовые заказы
        test_user = User.objects.filter(email='user1@test.ru').first()
        if test_user:
            test_orders_data = [
                {
                    'user': test_user,
                    'status': 'pending',
                    'total': Decimal('89999.00'),
                    'shipping_address': 'Москва, ул. Тестовая, д. 1'
                },
                {
                    'user': test_user,
                    'status': 'completed',
                    'total': Decimal('5999.00'),
                    'shipping_address': 'Москва, ул. Тестовая, д. 1'
                }
            ]
            
            for order_data in test_orders_data:
                order = Order.objects.create(**order_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Создан заказ #{order.id}')
                )

        self.stdout.write(
            self.style.SUCCESS('\n=== ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО ===\n')
        )
        self.stdout.write('Созданные данные:')
        self.stdout.write(f'- Пользователи: {User.objects.count()}')
        self.stdout.write(f'- Категории: {Category.objects.count()}')
        self.stdout.write(f'- Товары: {Product.objects.count()}')
        self.stdout.write(f'- Заказы: {Order.objects.count()}')
        self.stdout.write(f'- Фоновый контент: {BackgroundContent.objects.count()}')
        self.stdout.write('\nДанные для входа администратора:')
        self.stdout.write(f'Email: {admin_email}')
        self.stdout.write(f'Пароль: {admin_password}')