# CargoTrans - Система управления грузоперевозками

## Описание
CargoTrans - это веб-приложение для управления грузоперевозками, разработанное на Django. Система позволяет управлять автопарком, водителями, заказами и клиентами.

## Основные функции
- Управление автопарком (транспортные средства, типы транспорта, типы кузова)
- Управление водителями
- Управление заказами
- Управление клиентами и организациями
- Статистика и аналитика
- REST API для интеграции

## Технологии
- Python 3.11
- Django 5.0
- Django REST Framework
- SQLite
- pytest для тестирования
- Chart.js для визуализации

## Установка и запуск

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Примените миграции:
```bash
python manage.py migrate
```

4. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

5. Заполните базу данных тестовыми данными:
```bash
python manage.py populate_db
```

6. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Тестирование
Для запуска тестов используйте:
```bash
pytest
```

Для просмотра отчета о покрытии тестами откройте `coverage/index.html`

## API Endpoints
- `/api/vehicle-types/` - Типы транспортных средств
- `/api/body-types/` - Типы кузова
- `/api/vehicles/` - Транспортные средства
- `/api/drivers/` - Водители
- `/api/cargo-types/` - Типы грузов
- `/api/services/` - Услуги
- `/api/clients/` - Клиенты
- `/api/organizations/` - Организации
- `/api/orders/` - Заказы

## Разграничение прав
- Неавторизованные пользователи: только просмотр общей информации
- Авторизованные пользователи: просмотр информации о заказах и создание новых заказов
- Администраторы: полный доступ ко всем функциям системы

## Лицензия
MIT License 