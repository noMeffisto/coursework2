from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
import random
from main.models import (
    VehicleType, BodyType, Vehicle, Driver, CargoType,
    Service, Client, Order, Review, Promotion
)

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')

        # Create vehicle types
        vehicle_types = []
        vehicle_type_names = [
            'Грузовик', 'Фургон', 'Тягач', 'Микроавтобус', 'Спецтехника',
            'Рефрижератор', 'Эвакуатор', 'Самосвал', 'Автоцистерна', 'Платформа'
        ]
        for name in vehicle_type_names:
            vehicle_type, created = VehicleType.objects.get_or_create(
                name=name,
                defaults={'description': f'Транспортное средство типа {name.lower()} для различных видов перевозок'}
            )
            vehicle_types.append(vehicle_type)
            if created:
                self.stdout.write(f'Created vehicle type: {vehicle_type.name}')

        # Create body types
        body_types = []
        body_type_names = [
            'Тентованный', 'Изотермический', 'Рефрижератор', 'Цельнометаллический', 'Контейнер',
            'Открытый борт', 'Платформа', 'Фургон', 'Цистерна', 'Самосвальный'
        ]
        for name in body_type_names:
            body_type, created = BodyType.objects.get_or_create(
                name=name,
                defaults={'description': f'Тип кузова {name.lower()} для специализированных перевозок'}
            )
            body_types.append(body_type)
            if created:
                self.stdout.write(f'Created body type: {body_type.name}')

        # Create cargo types
        cargo_types = []
        cargo_type_data = [
            ('Продукты питания', 'Требуется соблюдение температурного режима', 'Санитарная книжка водителя'),
            ('Стройматериалы', 'Тяжелые грузы', 'Крепление груза'),
            ('Мебель', 'Хрупкий груз', 'Аккуратная погрузка/разгрузка'),
            ('Бытовая техника', 'Электроника', 'Защита от влаги'),
            ('Одежда', 'Легкий груз', 'Чистый кузов'),
            ('Автозапчасти', 'Запчасти и комплектующие', 'Защита от повреждений'),
            ('Медикаменты', 'Особый температурный режим', 'Лицензия на перевозку'),
            ('Химикаты', 'Опасные грузы', 'Допуск ADR'),
            ('Металлопрокат', 'Тяжелый груз', 'Усиленная платформа'),
            ('Зерно', 'Насыпной груз', 'Герметичный кузов')
        ]
        for name, desc, req in cargo_type_data:
            cargo_type, created = CargoType.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'special_requirements': req
                }
            )
            cargo_types.append(cargo_type)
            if created:
                self.stdout.write(f'Created cargo type: {cargo_type.name}')

        # Create vehicles
        vehicles = []
        brands = ['Volvo', 'Mercedes', 'MAN', 'Scania', 'DAF', 'Iveco', 'Ford', 'Renault', 'Kamaz', 'MAZ']
        models = ['FH16', 'Actros', 'TGX', 'R500', 'XF', 'Stralis', 'Cargo', 'T-Series', '5490', '5440']
        for i in range(10):
            vehicle = Vehicle.objects.create(
                type=random.choice(vehicle_types),
                body_type=random.choice(body_types),
                brand=brands[i],
                model=models[i],
                year=random.randint(2018, 2024),
                plate_number=f'{random.choice("ABCDEFGHIJK")}{random.randint(100,999)}{random.choice("ABCDEFGHIJK")}{random.randint(10,99)}',
                capacity=random.choice([3000, 5000, 10000, 15000, 20000]),
                is_available=random.choice([True, True, True, False])  # 75% шанс быть доступным
            )
            vehicles.append(vehicle)
            self.stdout.write(f'Created vehicle: {vehicle}')

        # Create users and drivers/clients
        for i in range(20):  # 10 водителей и 10 клиентов
            username = f'user{i+1}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password='testpass123',
                    first_name=f'Name{i+1}',
                    last_name=f'Surname{i+1}',
                    email=f'user{i+1}@example.com'
                )
                
                if i < 10:  # Первые 10 пользователей - водители
                    driver = Driver.objects.create(
                        user=user,
                        phone=f'+37529{random.randint(1000000,9999999)}',
                        experience=random.randint(1, 15),
                        categories=random.choice(['B,C', 'B,C,E', 'B,C,D,E']),
                        vehicle=vehicles[i] if i < len(vehicles) else None,
                        birth_date=date(random.randint(1970, 2000), random.randint(1, 12), random.randint(1, 28))
                    )
                    self.stdout.write(f'Created driver: {driver}')
                else:  # Остальные - клиенты
                    client = Client.objects.create(
                        user=user,
                        phone=f'+37529{random.randint(1000000,9999999)}',
                        address=f'ул. Примерная, д. {random.randint(1,100)}',
                        company_name=f'ООО Компания {i-9}' if random.choice([True, False]) else ''
                    )
                    self.stdout.write(f'Created client: {client}')

        # Create services
        services = []
        service_names = [
            'Городская доставка', 'Междугородняя перевозка', 'Международная перевозка',
            'Перевозка негабаритных грузов', 'Рефрижераторные перевозки',
            'Экспресс-доставка', 'Сборные грузы', 'Перевозка опасных грузов',
            'Перевозка стройматериалов', 'Квартирный переезд'
        ]
        for i, name in enumerate(service_names):
            service = Service.objects.create(
                name=name,
                description=f'Профессиональная услуга {name.lower()}',
                vehicle_type=vehicle_types[i],
                base_price=random.randint(5000, 50000),
                max_weight=random.randint(1000, 20000),
                max_volume=random.randint(10, 100),
                is_active=True
            )
            services.append(service)
            self.stdout.write(f'Created service: {service}')

        # Create orders
        statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        clients = Client.objects.all()
        drivers = Driver.objects.all()
        
        for i in range(10):
            status = random.choice(statuses)
            client = random.choice(clients)
            driver = random.choice(drivers) if status != 'pending' else None
            
            order = Order.objects.create(
                client=client,
                service=random.choice(services),
                driver=driver,
                cargo_type=random.choice(cargo_types),
                pickup_address=f'ул. Отправления, д. {random.randint(1,100)}',
                delivery_address=f'ул. Доставки, д. {random.randint(1,100)}',
                weight=random.randint(100, 10000),
                volume=random.randint(1, 50),
                status=status,
                total_price=random.randint(5000, 100000),
                notes=f'Заказ №{i+1}. Особые пожелания клиента.'
            )
            self.stdout.write(f'Created order: {order}')

        # Create reviews
        users = User.objects.all()
        for i in range(10):
            review = Review.objects.create(
                user=random.choice(users),
                text=f'Отличный сервис! Всем рекомендую. Отзыв №{i+1}',
                rating=random.randint(4, 5)
            )
            self.stdout.write(f'Created review: {review}')

        # Create promotions
        promo_names = [
            'ВЕСНА2024', 'ЛЕТО2024', 'ОСЕНЬ2024', 'ЗИМА2024',
            'НОВЫЙ2024', 'ПРАЗДНИК', 'ВЫХОДНОЙ', 'СЧАСТЛИВЫЙ',
            'БОНУС10', 'ПРОМО2024'
        ]
        for i, code in enumerate(promo_names):
            promotion = Promotion.objects.create(
                code=code,
                description=f'Скидка на все услуги! Промокод: {code}',
                discount_percent=random.randint(5, 20),
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=random.randint(30, 90)),
                is_active=True,
                max_uses=random.randint(50, 200),
                used_count=random.randint(0, 49)
            )
            self.stdout.write(f'Created promotion: {promotion}')

        self.stdout.write(self.style.SUCCESS('Successfully populated database')) 