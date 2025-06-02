from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from django.utils import timezone
from ..models import (
    VehicleType, BodyType, Vehicle, Driver, CargoType,
    Service, Client, Organization, Order
)

class ApiTests(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        
        # Создаем тестового клиента
        self.client_user = Client.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            address='Test Address',
            birth_date=date(1990, 1, 1)
        )
        
        # Создаем тестовые объекты
        self.vehicle_type = VehicleType.objects.create(
            name='Test Type',
            description='Test Description'
        )
        
        self.body_type = BodyType.objects.create(
            name='Test Body',
            description='Test Description'
        )
        
        self.vehicle = Vehicle.objects.create(
            vehicle_type=self.vehicle_type,
            body_type=self.body_type,
            brand='Test Brand',
            model='Test Model',
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
        
        # Создаем тестовый заказ
        self.order = Order.objects.create(
            client=self.client_user,
            service=self.service,
            cargo_type=self.cargo_type,
            vehicle=self.vehicle,
            pickup_address='Test Pickup',
            delivery_address='Test Delivery',
            pickup_date=timezone.now() + timedelta(days=1),
            delivery_date=timezone.now() + timedelta(days=2),
            cargo_weight=5.0,
            cargo_description='Test Cargo',
            price=1000.0,
            status='new'
        )
        
        # Инициализируем API клиент
        self.api_client = APIClient()

    def test_vehicle_type_list_authenticated(self):
        """Тест получения списка типов транспортных средств авторизованным пользователем"""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(reverse('vehicletype-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_vehicle_type_list_unauthenticated(self):
        """Тест получения списка типов транспортных средств неавторизованным пользователем"""
        response = self.api_client.get(reverse('vehicletype-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vehicle_type_create_admin(self):
        """Тест создания типа транспортного средства администратором"""
        self.api_client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Type',
            'description': 'New Description'
        }
        response = self.api_client.post(reverse('vehicletype-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VehicleType.objects.count(), 2)

    def test_vehicle_type_create_non_admin(self):
        """Тест создания типа транспортного средства обычным пользователем"""
        self.api_client.force_authenticate(user=self.user)
        data = {
            'name': 'New Type',
            'description': 'New Description'
        }
        response = self.api_client.post(reverse('vehicletype-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vehicle_list_filter(self):
        """Тест фильтрации списка транспортных средств"""
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(reverse('vehicle-list') + '?brand=Test Brand')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_vehicle_list_ordering(self):
        """Тест сортировки списка транспортных средств"""
        Vehicle.objects.create(
            vehicle_type=self.vehicle_type,
            body_type=self.body_type,
            brand='Another Brand',
            model='Test Model',
            year=2021,
            plate_number='TEST456',
            capacity=15.0
        )
        
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.get(reverse('vehicle-list') + '?ordering=year')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_order_create_validation(self):
        """Тест валидации при создании заказа"""
        self.api_client.force_authenticate(user=self.admin_user)
        
        data = {
            'client': self.client_user.id,
            'service': self.service.id,
            'cargo_type': self.cargo_type.id,
            'vehicle': self.vehicle.id,
            'pickup_address': 'Test Pickup',
            'delivery_address': 'Test Delivery',
            'pickup_date': '2024-01-01T10:00:00Z',
            'delivery_date': '2024-01-01T09:00:00Z',  # Дата доставки раньше даты загрузки
            'cargo_weight': 5.0,
            'cargo_description': 'Test Cargo',
            'price': 1000.0
        }
        
        response = self.api_client.post(reverse('order-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_statistics(self):
        """Тест получения статистики по клиентам"""
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.get(reverse('client-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('orders_count' in response.data['results'][0])
        self.assertTrue('total_spent' in response.data['results'][0]) 