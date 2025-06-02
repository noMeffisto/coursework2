from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from ..models import (
    VehicleType, BodyType, Vehicle, Driver, CargoType,
    Service, Client, Organization, Order
)

class VehicleTypeTests(TestCase):
    def test_vehicle_type_creation(self):
        vehicle_type = VehicleType.objects.create(
            name='Грузовик',
            description='Большой грузовик'
        )
        self.assertEqual(str(vehicle_type), 'Грузовик')

class BodyTypeTests(TestCase):
    def test_body_type_creation(self):
        body_type = BodyType.objects.create(
            name='Тентованный',
            description='Тентованный кузов'
        )
        self.assertEqual(str(body_type), 'Тентованный')

class VehicleTests(TestCase):
    def setUp(self):
        self.vehicle_type = VehicleType.objects.create(name='Грузовик')
        self.body_type = BodyType.objects.create(name='Тентованный')

    def test_vehicle_creation(self):
        vehicle = Vehicle.objects.create(
            vehicle_type=self.vehicle_type,
            body_type=self.body_type,
            brand='Volvo',
            model='FH16',
            year=2020,
            plate_number='A123BC',
            capacity=20.0,
            is_available=True
        )
        self.assertEqual(str(vehicle), 'Volvo FH16 (A123BC)')

    def test_invalid_year(self):
        with self.assertRaises(ValidationError):
            vehicle = Vehicle(
                vehicle_type=self.vehicle_type,
                body_type=self.body_type,
                brand='Volvo',
                model='FH16',
                year=1900,  # Год меньше минимального
                plate_number='A123BC',
                capacity=20.0
            )
            vehicle.full_clean()

class DriverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='driver1',
            password='testpass123',
            first_name='Иван',
            last_name='Иванов'
        )

    def test_driver_creation(self):
        driver = Driver.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            license_number='AB123456',
            experience=5,
            birth_date=date(1990, 1, 1)
        )
        self.assertEqual(str(driver), 'Иван Иванов (AB123456)')

    def test_invalid_phone_number(self):
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='123456',  # Неверный формат
                license_number='AB123456',
                experience=5,
                birth_date=date(1990, 1, 1)
            )
            driver.full_clean()

    def test_underage_driver(self):
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+375 (29) 123-45-67',
                license_number='AB123456',
                experience=0,
                birth_date=date.today() - timedelta(days=17*365)  # 17 лет
            )
            driver.full_clean()

class ClientTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='client1',
            password='testpass123'
        )

    def test_client_creation(self):
        client = Client.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            address='г. Минск, ул. Примерная, 1',
            birth_date=date(1990, 1, 1)
        )
        self.assertTrue(isinstance(client, Client))

    def test_underage_client(self):
        with self.assertRaises(ValidationError):
            client = Client(
                user=self.user,
                phone='+375 (29) 123-45-67',
                address='г. Минск, ул. Примерная, 1',
                birth_date=date.today() - timedelta(days=17*365)
            )
            client.full_clean()

class OrderTests(TestCase):
    def setUp(self):
        # Создаем необходимые объекты для тестирования заказов
        self.user = User.objects.create_user(username='testuser')
        self.client = Client.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            address='Test Address',
            birth_date=date(1990, 1, 1)
        )
        self.vehicle_type = VehicleType.objects.create(name='Test Type')
        self.body_type = BodyType.objects.create(name='Test Body')
        self.vehicle = Vehicle.objects.create(
            vehicle_type=self.vehicle_type,
            body_type=self.body_type,
            brand='Test',
            model='Test',
            year=2020,
            plate_number='TEST123',
            capacity=10.0
        )
        self.cargo_type = CargoType.objects.create(
            name='Test Cargo',
            description='Test Description'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            base_price=100.0
        )

    def test_order_creation(self):
        order = Order.objects.create(
            client=self.client,
            service=self.service,
            cargo_type=self.cargo_type,
            vehicle=self.vehicle,
            pickup_address='Test Pickup',
            delivery_address='Test Delivery',
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=2),
            cargo_weight=5.0,
            cargo_description='Test Cargo',
            price=1000.0
        )
        self.assertTrue(isinstance(order, Order))

    def test_invalid_dates(self):
        with self.assertRaises(ValidationError):
            order = Order(
                client=self.client,
                service=self.service,
                cargo_type=self.cargo_type,
                vehicle=self.vehicle,
                pickup_address='Test Pickup',
                delivery_address='Test Delivery',
                pickup_date=timezone.now() + timedelta(days=2),  # Дата загрузки позже выгрузки
                delivery_date=timezone.now() + timedelta(days=1),
                cargo_weight=5.0,
                cargo_description='Test Cargo',
                price=1000.0
            )
            order.full_clean() 