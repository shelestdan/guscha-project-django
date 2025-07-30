from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.cart.models import CartItem, Reservation

User = get_user_model()


class Command(BaseCommand):
    help = 'Test reservation creation'
    
    def handle(self, *args, **options):
        # Проверяем наличие пользователей и товаров
        user = User.objects.first()
        product = Product.objects.first()
        
        self.stdout.write(f'User: {user}')
        self.stdout.write(f'Product: {product}')
        
        if user and product:
            # Очищаем старые элементы корзины для этого пользователя
            CartItem.objects.filter(user=user).delete()
            
            # Создаем элемент корзины
            cart_item = CartItem.objects.create(
                user=user,
                product=product,
                quantity=1,
                price=product.price,  # Добавляем цену товара
                item_type='product'
            )
            self.stdout.write(f'Created CartItem: {cart_item}')
            
            # Проверяем количество элементов корзины и резервирований
            cart_count = CartItem.objects.count()
            reservation_count = Reservation.objects.count()
            
            self.stdout.write(f'CartItem count: {cart_count}')
            self.stdout.write(f'Reservation count: {reservation_count}')
            
            self.stdout.write(self.style.SUCCESS('Test completed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('No user or product found'))