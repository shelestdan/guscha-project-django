from django.test import TestCase, Client
from djmoney.money import Money

from apps.accounts.models import User
from apps.addresses.models import Address
from apps.orders.models import Order
from apps.cart.models import CartItem


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_endpoint_returns_healthy(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("status"), "healthy")
        self.assertEqual(payload.get("service"), "django")


class OrderSerializationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="buyer@example.com", password="Testpass123!"
        )
        self.billing_address = Address.objects.create(
            user=self.user,
            address_type="billing",
            first_name="Ivan",
            last_name="Petrov",
            address_line1="Lenina 1",
            address_line2="Office 2",
            city="Moscow",
            state="MO",
            postal_code="101000",
            country="Russia",
            phone="+79990000000",
            is_default=True,
        )
        self.shipping_address = Address.objects.create(
            user=self.user,
            address_type="shipping",
            first_name="Ivan",
            last_name="Petrov",
            address_line1="Nevsky 2",
            address_line2="Apt 5",
            city="Saint-Petersburg",
            state="SPB",
            postal_code="190000",
            country="Russia",
            phone="+79991111111",
        )

    def test_to_dict_serializes_addresses_and_totals(self):
        order = Order.objects.create(
            user=self.user,
            email="buyer@example.com",
            billing_address_obj=self.billing_address,
            shipping_address_obj=self.shipping_address,
            subtotal=Money("1000", "RUB"),
            tax=Money("0", "RUB"),
            shipping=Money("0", "RUB"),
            discount=Money("0", "RUB"),
            total=Money("1000", "RUB"),
        )

        data = order.to_dict()

        self.assertEqual(data["billing_address"], self.billing_address.full_address)
        self.assertEqual(
            data["shipping_address"], self.shipping_address.full_address
        )
        self.assertIsInstance(data["billing_address_obj"], dict)
        self.assertIsInstance(data["shipping_address_obj"], dict)
        self.assertEqual(
            data["billing_address_obj"]["address_line1"], "Lenina 1"
        )
        self.assertEqual(
            data["shipping_address_obj"]["address_line1"], "Nevsky 2"
        )
        self.assertEqual(data["total"], 1000.0)
        self.assertTrue(data["order_number"].startswith("ORD-"))


class CartItemTotalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cartuser@example.com", password="Testpass123!"
        )

    def test_total_multiplies_money_by_quantity(self):
        item = CartItem.objects.create(
            user=self.user,
            quantity=3,
            price=Money("150.00", "RUB"),
            item_type="product",
        )

        self.assertEqual(item.total, Money("450.00", "RUB"))

