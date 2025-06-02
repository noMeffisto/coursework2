from django.core.management.base import BaseCommand
from main.models import VehicleType, BodyType, Vehicle, Driver, CargoType, Service, Client, Organization, Order, Review
from django.contrib.auth.models import User
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Populate database with test data'

    def handle(self, *args, **kwargs):
        # Создаем суперпользователя
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='vooitenkoo',
                email='admin@example.com',
                password='1234567890'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))

        # Создаем типы транспортных средств
        vehicle_types = [
            VehicleType.objects.create(name='Грузовик'),
            VehicleType.objects.create(name='Фургон'),
            VehicleType.objects.create(name='Рефрижератор'),
            VehicleType.objects.create(name='Автоцистерна'),
            VehicleType.objects.create(name='Самосвал'),
            VehicleType.objects.create(name='Лесовоз'),
            VehicleType.objects.create(name='Автовоз'),
            VehicleType.objects.create(name='Контейнеровоз'),
            VehicleType.objects.create(name='Бетоносмеситель'),
            VehicleType.objects.create(name='Эвакуатор'),
        ]

        # Создаем типы кузовов
        body_types = [
            BodyType.objects.create(name='Тентованный'),
            BodyType.objects.create(name='Цельнометаллический'),
            BodyType.objects.create(name='Изотермический'),
            BodyType.objects.create(name='Рефрижераторный'),
            BodyType.objects.create(name='Контейнерный'),
            BodyType.objects.create(name='Платформа'),
            BodyType.objects.create(name='Самосвальный'),
            BodyType.objects.create(name='Цистерна'),
            BodyType.objects.create(name='Лесовозный'),
            BodyType.objects.create(name='Автовозный'),
        ]

        # Создаем транспортные средства
        vehicles = []
        for i in range(10):
            vehicle = Vehicle.objects.create(
                vehicle_type=random.choice(vehicle_types),
                body_type=random.choice(body_types),
                brand=random.choice(['MAN', 'Volvo', 'Mercedes', 'Scania', 'DAF']),
                model=f'Model-{i+1}',
                year=random.randint(2015, 2023),
                capacity=random.randint(5000, 20000),
                plate_number=f'AB{random.randint(1000, 9999)}CD'
            )
            vehicles.append(vehicle)

        # Создаем водителей
        drivers = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'driver{i+1}',
                password='testpass123',
                first_name=f'Имя{i+1}',
                last_name=f'Фамилия{i+1}'
            )
            driver = Driver.objects.create(
                user=user,
                phone=f'+375 (29) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                license_number=f'DL{random.randint(100000, 999999)}',
                experience=random.randint(2, 20),
                birth_date=date(1980 + i, 1, 1)
            )
            driver.vehicles.add(random.choice(vehicles))
            drivers.append(driver)

        # Создаем типы грузов
        cargo_types = [
            CargoType.objects.create(name='Продукты питания'),
            CargoType.objects.create(name='Строительные материалы'),
            CargoType.objects.create(name='Мебель'),
            CargoType.objects.create(name='Техника'),
            CargoType.objects.create(name='Одежда'),
            CargoType.objects.create(name='Автозапчасти'),
            CargoType.objects.create(name='Химические вещества'),
            CargoType.objects.create(name='Металлопрокат'),
            CargoType.objects.create(name='Лесоматериалы'),
            CargoType.objects.create(name='Сельхозпродукция'),
        ]

        # Создаем услуги
        services = [
            Service.objects.create(name='Доставка', description='Стандартная доставка груза', base_price=100),
            Service.objects.create(name='Экспресс-доставка', description='Срочная доставка груза', base_price=200),
            Service.objects.create(name='Погрузка/разгрузка', description='Услуги грузчиков', base_price=50),
            Service.objects.create(name='Упаковка', description='Упаковка груза', base_price=30),
            Service.objects.create(name='Хранение', description='Временное хранение груза', base_price=20),
            Service.objects.create(name='Страхование', description='Страхование груза', base_price=80),
            Service.objects.create(name='Таможенное оформление', description='Таможенное оформление груза', base_price=150),
            Service.objects.create(name='Сборные грузы', description='Перевозка сборных грузов', base_price=120),
            Service.objects.create(name='Негабаритные грузы', description='Перевозка негабаритных грузов', base_price=300),
            Service.objects.create(name='Рефрижераторные перевозки', description='Перевозка грузов с температурным режимом', base_price=250),
        ]

        # Создаем организации
        organizations = []
        for i in range(10):
            org = Organization.objects.create(
                name=f'Компания {i+1}',
                address=f'ул. Примерная, {i+1}',
                phone=f'+375 (29) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                email=f'company{i+1}@example.com',
                inn=f'{random.randint(100000000, 999999999)}'
            )
            organizations.append(org)

        # Создаем клиентов
        clients = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'client{i+1}',
                password='testpass123',
                first_name=f'Клиент{i+1}',
                last_name=f'Фамилия{i+1}'
            )
            client = Client.objects.create(
                user=user,
                phone=f'+375 (29) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                birth_date=date(1980 + i, 1, 1),
                address=f'г. Минск, ул. Клиентская, {i+1}'
            )
            clients.append(client)

        # Создаем заказы
        orders = []
        for i in range(15):
            order = Order.objects.create(
                client=random.choice(clients),
                driver=random.choice(drivers),
                vehicle=random.choice(vehicles),
                cargo_type=random.choice(cargo_types),
                service=random.choice(services),
                pickup_address=f'ул. Отправления, {i+1}',
                delivery_address=f'ул. Доставки, {i+1}',
                pickup_date=date.today() + timedelta(days=random.randint(1, 30)),
                delivery_date=date.today() + timedelta(days=random.randint(31, 60)),
                status=random.choice(['new', 'assigned', 'in_progress', 'completed', 'cancelled']),
                cargo_weight=random.randint(100, 5000),
                cargo_description=f'Тестовый груз {i+1}',
                price=random.randint(100, 1000)
            )
            orders.append(order)

        # Создаем отзывы для завершенных заказов
        comments = [
            'Отличный сервис! Водитель был очень вежлив и пунктуален.',
            'Груз доставлен вовремя и в целости.',
            'Хорошая работа, но есть над чем поработать.',
            'Неплохо, но можно лучше.',
            'Все прошло отлично, рекомендую!',
            'Водитель - профессионал своего дела.',
            'Доставка выполнена в срок, претензий нет.',
            'Сервис на высоте!',
            'Спасибо за качественную работу!',
            'Буду обращаться еще!'
        ]

        for order in orders:
            if order.status == 'completed':
                Review.objects.create(
                    order=order,
                    client=order.client,
                    driver=order.driver,
                    rating=random.randint(3, 5),
                    comment=random.choice(comments)
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with test data')) 