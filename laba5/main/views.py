from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum, Q, F, Min, Max
from django.db.models.functions import ExtractYear, ExtractMonth
from django.utils import timezone
from django.contrib import messages
from .models import Order, Client, Vehicle, CargoType, Service, Driver, VehicleType, BodyType, Review, Promotion, Schedule, News, AboutPageContent, SiteSettings
from .forms import UserRegistrationForm, OrderForm, ServiceFilterForm, ReviewForm, NewsForm
import logging
from .services.external_api import get_weather_for_city, get_coordinates
from django.contrib.admin.views.decorators import staff_member_required

import matplotlib
matplotlib.use('Agg') # Устанавливаем бэкенд Agg перед импортом pyplot
import matplotlib.pyplot as plt

import io
import base64
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView
import pytz
from django.http import JsonResponse
import time

logger = logging.getLogger(__name__)

def index(request):
    logger.info("Accessing home page")
    latest_news = News.objects.filter(is_published=True).order_by('-created_at')[:3]
    return render(request, 'main/index.html', {
        'latest_news': latest_news
    })

def about(request):
    logger.info("Accessing about page")
    content = AboutPageContent.objects.first()
    if not content:
        # Если в базе нет данных, можно использовать значения по умолчанию или создать объект
        # Для простоты пока передадим пустые значения или создадим объект на лету
        # content = AboutPageContent.objects.create(title="О нашей компании", content="Информация о компании скоро появится.")
        # Либо передаем в контекст None и обрабатываем в шаблоне
        pass # Оставляем content=None, шаблон должен это обработать
    return render(request, 'main/about.html', {'about_content': content})

def news(request):
    logger.info("Accessing news page")
    all_news = News.objects.filter(is_published=True).order_by('-created_at')
    # TODO: Добавить пагинацию, если новостей много
    return render(request, 'main/news.html', {'news_list': all_news})

def dictionary(request):
    logger.info("Accessing dictionary page")
    return render(request, 'main/dictionary.html')

def contacts(request):
    logger.info("Accessing contacts page")
    return render(request, 'main/contacts.html')

def vacancies(request):
    logger.info("Accessing vacancies page")
    return render(request, 'main/vacancies.html')

@login_required
def reviews(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        rating = request.POST.get('rating')
        
        if text and rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    Review.objects.create(
                        user=request.user,
                        text=text,
                        rating=rating
                    )
                    logger.info(f'New review created by user {request.user.username}')
                    messages.success(request, 'Спасибо за ваш отзыв!')
                else:
                    messages.error(request, 'Оценка должна быть от 1 до 5')
            except ValueError:
                messages.error(request, 'Некорректная оценка')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля')
    
    reviews = Review.objects.select_related('user').all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    context = {
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0
    }
    
    return render(request, 'main/reviews.html', context)

def promotions(request):
    logger.info("Accessing promotions page")
    now = timezone.now()
    active_promotions = Promotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).annotate(
        uses_left=F('max_uses') - F('used_count')
    ).filter(
        Q(max_uses__isnull=True) | Q(uses_left__gt=0)
    ).order_by('end_date')
    
    return render(request, 'main/promotions/list.html', {
        'promotions': active_promotions
    })

def privacy(request):
    logger.info("Accessing privacy page")
    return render(request, 'main/privacy.html')

def terms(request):
    logger.info("Accessing terms page")
    return render(request, 'main/terms.html')

def services(request):
    logger.info("Accessing services page")
    return render(request, 'main/services.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Вы успешно зарегистрированы и вошли в систему!')
                logger.info(f'New user registered: {user.username}')
                return redirect('main:home')
            except Exception as e:
                logger.error(f'Error during registration: {str(e)}')
                messages.error(request, 'Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'main/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('main:home')

@login_required
def driver_profile(request):
    return render(request, 'main/driver_profile.html')

@login_required
def client_profile(request):
    return render(request, 'main/client_profile.html')

@login_required
def statistics(request):
    plt.close('all')
    
    # Статистика по заказам
    orders = Order.objects.all()
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    avg_order_price = orders.aggregate(Avg('total_price'))['total_price__avg'] or 0
    
    # Статистика по водителям
    drivers = Driver.objects.all()
    total_drivers = drivers.count()
    avg_driver_experience = drivers.aggregate(Avg('experience'))['experience__avg'] or 0
    
    # Статистика по транспорту
    vehicles = Vehicle.objects.all()
    total_vehicles = vehicles.count()
    available_vehicles = vehicles.filter(is_available=True).count()
    
    # Функция для кодирования графика в base64
    def get_graph_base64():
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        return base64.b64encode(image_png).decode()

    # График 1: Количество заказов по месяцам
    orders_by_month = (
        Order.objects
        .annotate(month=ExtractMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    plt.figure(figsize=(10, 6))
    if orders_by_month:
        months = []
        counts = []
        month_names = ['Янв', 'Фев', 'Март', 'Апр', 'Май', 'Июнь', 'Июль', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        
        for item in orders_by_month:
            if item['month'] and item['count']:
                months.append(month_names[item['month']-1])
                counts.append(int(item['count']))
        
        if months and counts:
            plt.bar(months, counts, color='#007bff', alpha=0.7)
            plt.title('Количество заказов по месяцам', pad=20)
            plt.xlabel('Месяц')
            plt.ylabel('Количество заказов')
            
            # Добавляем значения над столбцами
            for i, count in enumerate(counts):
                plt.text(i, count, str(count), ha='center', va='bottom')
            
            # Настраиваем внешний вид
            plt.grid(True, axis='y', alpha=0.3, linestyle='--')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            orders_by_month_graph = get_graph_base64()
        else:
            orders_by_month_graph = None
    else:
        orders_by_month_graph = None
    plt.close()

    # График 2: Распределение заказов по статусам
    status_counts = orders.values('status').annotate(count=Count('id'))
    
    plt.figure(figsize=(8, 8))
    if status_counts:
        statuses = []
        counts = []
        for item in status_counts:
            if item['status'] and item['count']:
                status_display = dict(Order.STATUS_CHOICES).get(item['status'], item['status'])
                statuses.append(status_display)
                counts.append(int(item['count']))
        
        if statuses and counts:
            plt.pie(counts, labels=statuses, autopct='%1.1f%%')
            plt.title('Распределение заказов по статусам')
            status_distribution_graph = get_graph_base64()
        else:
            status_distribution_graph = None
    else:
        status_distribution_graph = None
    plt.close()

    # График 3: Средняя стоимость заказа по типам транспорта
    avg_price_by_vehicle = (
        Order.objects
        .filter(driver__isnull=False)
        .values('driver__vehicle__type__name')
        .annotate(avg_price=Avg('total_price'))
        .filter(driver__vehicle__type__name__isnull=False)
        .order_by('-avg_price')
    )
    
    plt.figure(figsize=(10, 6))
    if avg_price_by_vehicle:
        vehicle_types = []
        prices = []
        for item in avg_price_by_vehicle:
            if item['driver__vehicle__type__name'] and item['avg_price']:
                vehicle_types.append(item['driver__vehicle__type__name'])
                prices.append(float(item['avg_price']))
        
        if vehicle_types and prices:
            plt.bar(vehicle_types, prices)
            plt.title('Средняя стоимость заказа по типам транспорта')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            price_by_vehicle_graph = get_graph_base64()
        else:
            price_by_vehicle_graph = None
    else:
        price_by_vehicle_graph = None
    plt.close()
    
    # График 4: Топ-5 активных клиентов по количеству заказов
    top_clients_data = (
        Client.objects.annotate(num_orders=Count('order'))
        .filter(num_orders__gt=0)
        .order_by('-num_orders')[:5]
    )

    top_clients_graph = None
    if top_clients_data:
        client_names = []
        order_counts = []
        for client_entry in top_clients_data:
            # Пытаемся получить полное имя, если нет - username
            name_display = client_entry.user.get_full_name() or client_entry.user.username
            if client_entry.company_name:
                name_display = f"{name_display} ({client_entry.company_name})"
            client_names.append(name_display)
            order_counts.append(client_entry.num_orders)
        
        if client_names and order_counts:
            plt.figure(figsize=(10, 7)) # Может потребоватьсяadjust размер
            bars = plt.barh(client_names, order_counts, color='#28a745') # Используем зеленый цвет, как в CSS
            plt.xlabel('Количество заказов')
            plt.title('Топ-5 активных клиентов')
            plt.gca().invert_yaxis() # Чтобы самый активный был сверху
            # Добавляем значения на столбцы
            for bar in bars:
                plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                         f'{bar.get_width()}', 
                         va='center', ha='left')
            plt.tight_layout()
            top_clients_graph = get_graph_base64()
    plt.close() # Закрываем текущую фигуру

    context = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'avg_order_price': round(avg_order_price, 2),
        'total_drivers': total_drivers,
        'avg_driver_experience': round(avg_driver_experience, 1),
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'orders_by_month_graph': orders_by_month_graph,
        'status_distribution_graph': status_distribution_graph,
        'price_by_vehicle_graph': price_by_vehicle_graph,
        'top_clients_graph': top_clients_graph,
        'request': request,
        'timestamp': int(time.time()),
    }
    
    logger.info('Statistics page accessed')
    return render(request, 'main/statistics.html', context)

def privacy_policy(request):
    return render(request, 'main/privacy.html')

# Водительский функционал
@login_required
def driver_schedule(request):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен. Вы не являетесь водителем.')
        return redirect('main:home')
    
    driver = request.user.driver
    today = timezone.now().date()
    
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        is_available = request.POST.get('is_available', '') == 'on'
        notes = request.POST.get('notes', '')
        
        Schedule.objects.create(
            driver=driver,
            date=date,
            start_time=start_time,
            end_time=end_time,
            is_available=is_available,
            notes=notes
        )
        messages.success(request, 'Расписание успешно обновлено')
        return redirect('main:driver_schedule')
    
    # Получаем расписание на следующие 7 дней
    schedules = Schedule.objects.filter(
        driver=driver,
        date__gte=today,
        date__lte=today + timedelta(days=7)
    ).order_by('date', 'start_time')
    
    context = {
        'schedules': schedules,
        'today': today,
        'week_dates': [today + timedelta(days=x) for x in range(8)]
    }
    return render(request, 'main/driver/schedule.html', context)

@login_required
def driver_orders(request):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен. Вы не являетесь водителем.')
        return redirect('main:home')
    
    driver = request.user.driver
    status_filter = request.GET.get('status', '')
    
    orders = Order.objects.filter(driver=driver)
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'main/driver/orders.html', context)

@login_required
def driver_clients(request):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен')
        return redirect('main:home')
    
    clients = Client.objects.filter(
        order__driver=request.user.driver
    ).distinct()
    
    return render(request, 'main/driver/clients.html', {
        'clients': clients
    })

@login_required
def driver_cargo(request):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен')
        return redirect('main:home')
    
    cargo_types = CargoType.objects.filter(
        order__driver=request.user.driver
    ).distinct()
    
    return render(request, 'main/driver/cargo.html', {
        'cargo_types': cargo_types
    })

# Клиентский функционал
@login_required
def service_catalog(request):
    form = ServiceFilterForm(request.GET)
    services = Service.objects.all()
    
    if form.is_valid():
        if form.cleaned_data.get('min_price'):
            services = services.filter(base_price__gte=form.cleaned_data['min_price'])
        if form.cleaned_data.get('max_price'):
            services = services.filter(base_price__lte=form.cleaned_data['max_price'])
        if form.cleaned_data.get('category'):
            services = services.filter(vehicle_types=form.cleaned_data['category'])
    
    return render(request, 'main/services/catalog.html', {
        'services': services,
        'form': form
    })

@login_required
def purchase_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    
    if not hasattr(request.user, 'client'):
        messages.error(request, 'Только клиенты могут заказывать услуги')
        return redirect('main:service_catalog')
    
    if request.method == 'POST':
        form = OrderForm(request.POST, service=service)
        if form.is_valid():
            order = form.save(commit=False)
            order.client = request.user.client
            order.status = 'pending'
            try:
                order.save()
                messages.success(request, 'Заказ успешно создан')
                return redirect('main:client_orders')
            except Exception as e:
                logger.error(f'Error creating order: {str(e)}')
                messages.error(request, 'Произошла ошибка при создании заказа. Пожалуйста, попробуйте снова.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = OrderForm(service=service)
    
    return render(request, 'main/services/purchase.html', {
        'service': service,
        'form': form
    })

@login_required
def client_orders(request):
    if not hasattr(request.user, 'client'):
        messages.error(request, 'Доступ запрещен')
        return redirect('main:home')
    
    orders = Order.objects.filter(
        client=request.user.client
    ).order_by('-created_at')
    
    return render(request, 'main/client/orders.html', {
        'orders': orders
    })

@login_required
def client_promotions(request):
    if not hasattr(request.user, 'client'):
        messages.error(request, 'Доступ запрещен')
        return redirect('main:home')
    
    # В будущем здесь будет модель для промокодов
    promotions = []
    
    return render(request, 'main/client/promotions.html', {
        'promotions': promotions
    })

# Общая информация
def vehicle_list(request):
    vehicles = Vehicle.objects.select_related('type', 'body_type').all()
    vehicle_types = VehicleType.objects.all()
    body_types = BodyType.objects.all()
    
    type_filter = request.GET.get('type')
    body_filter = request.GET.get('body')
    available = request.GET.get('available')
    
    if type_filter:
        vehicles = vehicles.filter(type_id=type_filter)
    if body_filter:
        vehicles = vehicles.filter(body_type_id=body_filter)
    if available:
        vehicles = vehicles.filter(is_available=True)
    
    return render(request, 'main/vehicles/list.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types,
        'body_types': body_types
    })

def driver_list(request):
    drivers = Driver.objects.annotate(
        orders_count=Count('orders'),
        rating=Avg('user__review__rating')
    )
    
    experience_filter = request.GET.get('experience')
    if experience_filter:
        drivers = drivers.filter(experience__gte=experience_filter)
    
    return render(request, 'main/drivers/list.html', {
        'drivers': drivers
    })

def service_categories(request):
    categories = VehicleType.objects.annotate(
        services_count=Count('service'),
        min_price=Min('service__base_price', default=0),
        max_price=Max('service__base_price', default=0)
    )
    
    return render(request, 'main/services/categories.html', {
        'categories': categories
    })

def additional_services(request):
    services = Service.objects.filter(
        Q(name__icontains='дополнительн') |
        Q(description__icontains='дополнительн')
    )
    
    return render(request, 'main/services/additional.html', {
        'services': services
    })

@login_required
def add_review(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if not hasattr(request.user, 'client') or order.client != request.user.client:
        messages.error(request, 'У вас нет прав для добавления отзыва к этому заказу')
        return redirect('main:client_orders')
    
    if order.status != 'completed':
        messages.error(request, 'Отзыв можно оставить только для завершенного заказа')
        return redirect('main:client_orders')
    
    if hasattr(order, 'review'):
        messages.error(request, 'Вы уже оставили отзыв к этому заказу')
        return redirect('main:client_orders')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.save()
            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('main:reviews')
    else:
        form = ReviewForm()
    
    return render(request, 'main/reviews/add_review.html', {
        'form': form,
        'order': order
    })

@login_required
def apply_promotion(request, order_id):
    if not request.method == 'POST':
        return redirect('main:client_orders')
    
    order = get_object_or_404(Order, id=order_id, client=request.user.client)
    if order.status != 'pending':
        messages.error(request, 'Промокод можно применить только к новому заказу')
        return redirect('main:client_orders')
    
    promo_code = request.POST.get('promo_code')
    if not promo_code:
        messages.error(request, 'Введите промокод')
        return redirect('main:client_orders')
    
    try:
        promotion = Promotion.objects.get(code=promo_code, is_active=True)
        
        if not promotion.is_valid():
            messages.error(request, 'Промокод недействителен или срок его действия истек')
            return redirect('main:client_orders')
        
        
        original_price = order.total_price
        discount = (original_price * promotion.discount_percent) / 100
        order.total_price = original_price - discount
        order.save()
        
        promotion.used_count += 1
        promotion.save()
        
        messages.success(request, f'Промокод успешно применен! Скидка: {discount:.2f} ₽')
        
    except Promotion.DoesNotExist:
        messages.error(request, 'Промокод не найден')
    
    return redirect('main:client_orders')

@login_required
def cancel_order(request, order_id):
    if not request.method == 'POST':
        return redirect('main:client_orders')
    
    if not hasattr(request.user, 'client'):
        messages.error(request, 'Только клиенты могут отменять заказы')
        return redirect('main:home')
    
    order = get_object_or_404(Order, id=order_id, client=request.user.client)
    
    if order.status != 'pending':
        messages.error(request, 'Можно отменить только новый заказ')
        return redirect('main:client_orders')
    
    order.status = 'cancelled'
    order.save()
    
    messages.success(request, f'Заказ #{order.id} успешно отменен')
    return redirect('main:client_orders')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему')
            return redirect('main:home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'main/auth/login.html')

@login_required
def update_order_status(request, order_id):
    if not request.method == 'POST':
        return redirect('main:driver_schedule')
    
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен. Вы не являетесь водителем.')
        return redirect('main:home')
    
    order = get_object_or_404(Order, id=order_id, driver=request.user.driver)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Order.STATUS_CHOICES):
        messages.error(request, 'Некорректный статус')
        return redirect('main:driver_schedule')
    
    # Проверяем логику перехода статусов
    if order.status == 'pending' and new_status != 'in_progress':
        messages.error(request, 'Заказ можно только начать выполнять')
        return redirect('main:driver_schedule')
    
    if order.status == 'in_progress' and new_status != 'completed':
        messages.error(request, 'Заказ можно только завершить')
        return redirect('main:driver_schedule')
    
    order.status = new_status
    order.save()
    
    messages.success(request, f'Статус заказа #{order.id} обновлен на {dict(Order.STATUS_CHOICES)[new_status]}')
    return redirect('main:driver_schedule')

@login_required
@staff_member_required
def delete_driver(request, driver_id):
    if request.method == 'POST':
        try:
            driver = Driver.objects.get(id=driver_id)
            
            driver_user = driver.user
            driver.delete()
            messages.success(request, f'Водитель {driver_user.get_full_name()} успешно удален.')
        except Driver.DoesNotExist:
            messages.error(request, 'Водитель не найден.')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении водителя: {e}')
    return redirect('main:driver_list')

@login_required
@staff_member_required
def delete_service(request, service_id):
    if request.method == 'POST':
        try:
            service = Service.objects.get(id=service_id)
            service_name = service.name
            service.delete()
            messages.success(request, f'Услуга "{service_name}" успешно удалена.')
        except Service.DoesNotExist:
            messages.error(request, 'Услуга не найдена.')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении услуги: {e}')
    # Предполагаем, что есть страница со списком услуг с именем 'service_catalog'
    # или 'service_list'. Используем 'service_catalog' на основе main/urls.py.
    return redirect('main:service_catalog')

def vehicle_detail_by_plate(request, plate_number):
    try:
        vehicle = Vehicle.objects.select_related('type', 'body_type').get(plate_number=plate_number)
        logger.info(f'Vehicle found by plate number: {plate_number}')
        return render(request, 'main/vehicles/detail.html', {'vehicle': vehicle})
    except Vehicle.DoesNotExist:
        logger.warning(f'Vehicle not found by plate number: {plate_number}')
        messages.error(request, 'Транспортное средство с таким номером не найдено.')
        return redirect('main:vehicle_list')

@staff_member_required
def admin_orders(request):
    orders = Order.objects.select_related('client', 'driver', 'service', 'cargo_type').all()
    drivers = Driver.objects.select_related('user', 'vehicle').all()
    services = Service.objects.all()
    cargo_types = CargoType.objects.all()
    clients = Client.objects.select_related('user').all()

    if request.method == 'POST':
        if 'create_order' in request.POST:
            try:
                order = Order.objects.create(
                    client_id=request.POST.get('client'),
                    service_id=request.POST.get('service'),
                    driver_id=request.POST.get('driver'),
                    cargo_type_id=request.POST.get('cargo_type'),
                    pickup_address=request.POST.get('pickup_address'),
                    delivery_address=request.POST.get('delivery_address'),
                    weight=float(request.POST.get('weight')),
                    volume=float(request.POST.get('volume')),
                    status=request.POST.get('status'),
                    total_price=float(request.POST.get('total_price')),
                    notes=request.POST.get('notes', ''),
                    scheduled_date=request.POST.get('scheduled_date') or None,
                    scheduled_time=request.POST.get('scheduled_time') or None
                )
                messages.success(request, f'Заказ #{order.id} успешно создан')
                return redirect('main:admin_orders')
            except Exception as e:
                messages.error(request, f'Ошибка при создании заказа: {str(e)}')
        
        elif 'delete_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id)
                order.delete()
                messages.success(request, f'Заказ #{order_id} успешно удален')
            except Order.DoesNotExist:
                messages.error(request, 'Заказ не найден')
            return redirect('main:admin_orders')

        elif 'assign_driver' in request.POST:
            order_id = request.POST.get('order_id')
            driver_id = request.POST.get('driver_id')
            try:
                order = Order.objects.get(id=order_id)
                if driver_id:
                    driver = Driver.objects.get(id=driver_id)
                    order.driver = driver
                    order.status = 'in_progress'
                    order.save()
                    messages.success(request, f'Водитель назначен на заказ #{order_id}')
                else:
                    order.driver = None
                    order.status = 'pending'
                    order.save()
                    messages.success(request, f'Водитель снят с заказа #{order_id}')
            except (Order.DoesNotExist, Driver.DoesNotExist):
                messages.error(request, 'Заказ или водитель не найден')
            return redirect('main:admin_orders')

    context = {
        'orders': orders,
        'drivers': drivers,
        'services': services,
        'cargo_types': cargo_types,
        'clients': clients,
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'main/management/orders.html', context)

@staff_member_required
def admin_reviews(request):
    reviews = Review.objects.select_related('user').all()
    
    if request.method == 'POST' and 'delete_review' in request.POST:
        review_id = request.POST.get('review_id')
        try:
            review = Review.objects.get(id=review_id)
            review.delete()
            messages.success(request, 'Отзыв успешно удален')
        except Review.DoesNotExist:
            messages.error(request, 'Отзыв не найден')
        return redirect('main:admin_reviews')
    
    return render(request, 'main/management/reviews.html', {'reviews': reviews})

@staff_member_required
def admin_services(request):
    services = Service.objects.select_related('vehicle_type').all()
    vehicle_types = VehicleType.objects.all()
    
    if request.method == 'POST':
        if 'delete_service' in request.POST:
            service_id = request.POST.get('service_id')
            try:
                service = Service.objects.get(id=service_id)
                service.delete()
                messages.success(request, 'Услуга успешно удалена')
            except Service.DoesNotExist:
                messages.error(request, 'Услуга не найдена')
            return redirect('main:admin_services')
        
        elif 'create_service' in request.POST:
            try:
                service = Service.objects.create(
                    name=request.POST.get('name'),
                    description=request.POST.get('description'),
                    vehicle_type_id=request.POST.get('vehicle_type'),
                    base_price=float(request.POST.get('base_price')),
                    max_weight=float(request.POST.get('max_weight')),
                    max_volume=float(request.POST.get('max_volume')),
                    is_active=bool(request.POST.get('is_active'))
                )
                messages.success(request, f'Услуга "{service.name}" успешно создана')
                return redirect('main:admin_services')
            except Exception as e:
                messages.error(request, f'Ошибка при создании услуги: {str(e)}')
    
    context = {
        'services': services,
        'vehicle_types': vehicle_types
    }
    return render(request, 'main/management/services.html', context)

@staff_member_required
def admin_vehicles(request):
    vehicles = Vehicle.objects.select_related('type', 'body_type').all()
    vehicle_types = VehicleType.objects.all()
    body_types = BodyType.objects.all()
    
    if request.method == 'POST':
        if 'delete_vehicle' in request.POST:
            vehicle_id = request.POST.get('vehicle_id')
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                vehicle.delete()
                messages.success(request, 'Транспортное средство успешно удалено')
            except Vehicle.DoesNotExist:
                messages.error(request, 'Транспортное средство не найдено')
            return redirect('main:admin_vehicles')
        
        elif 'create_vehicle' in request.POST:
            try:
                vehicle = Vehicle.objects.create(
                    type_id=request.POST.get('type'),
                    body_type_id=request.POST.get('body_type'),
                    brand=request.POST.get('brand'),
                    model=request.POST.get('model'),
                    year=int(request.POST.get('year')),
                    plate_number=request.POST.get('plate_number'),
                    capacity=float(request.POST.get('capacity')),
                    is_available=bool(request.POST.get('is_available'))
                )
                if 'image' in request.FILES:
                    vehicle.image = request.FILES['image']
                    vehicle.save()
                messages.success(request, f'Транспортное средство {vehicle.brand} {vehicle.model} успешно создано')
                return redirect('main:admin_vehicles')
            except Exception as e:
                messages.error(request, f'Ошибка при создании транспортного средства: {str(e)}')
    
    context = {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types,
        'body_types': body_types
    }
    return render(request, 'main/management/vehicles.html', context)

def set_timezone(request):
    if request.method == 'POST':
        timezone_name = request.POST.get('timezone')
        if timezone_name in pytz.all_timezones:
            request.session['user_timezone'] = timezone_name
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def available_orders(request):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен. Вы не являетесь водителем.')
        return redirect('main:home')
    
    # Получаем все заказы со статусом 'pending' и без назначенного водителя
    available_orders = Order.objects.filter(
        status='pending',
        driver__isnull=True
    ).select_related('service', 'cargo_type', 'client')
    
    return render(request, 'main/driver/available_orders.html', {
        'available_orders': available_orders
    })

@login_required
def take_order(request, order_id):
    if not hasattr(request.user, 'driver'):
        messages.error(request, 'Доступ запрещен. Вы не являетесь водителем.')
        return redirect('main:home')
    
    if request.method != 'POST':
        return redirect('main:available_orders')
    
    try:
        order = Order.objects.get(
            id=order_id,
            status='pending',
            driver__isnull=True
        )
        
        # Проверяем, что водитель не занят другим заказом
        if Order.objects.filter(
            driver=request.user.driver,
            status='in_progress'
        ).exists():
            messages.error(request, 'У вас уже есть активный заказ')
            return redirect('main:available_orders')
        
        order.driver = request.user.driver
        order.status = 'in_progress'
        order.save()
        
        messages.success(request, f'Вы успешно взяли заказ #{order.id}')
        return redirect('main:driver_orders')
        
    except Order.DoesNotExist:
        messages.error(request, 'Заказ не найден или уже взят другим водителем')
        return redirect('main:available_orders')

@staff_member_required
def admin_drivers(request):
    drivers = Driver.objects.select_related('user', 'vehicle').all()
    # Получаем доступные транспортные средства (не назначенные другим водителям)
    available_vehicles = Vehicle.objects.filter(
        Q(driver__isnull=True) | Q(driver__in=drivers)
    ).select_related('type', 'body_type')

    if request.method == 'POST' and 'assign_vehicle' in request.POST:
        driver_id = request.POST.get('driver_id')
        vehicle_id = request.POST.get('vehicle_id')
        try:
            driver = Driver.objects.get(id=driver_id)
            
            # Если был выбран транспорт
            if vehicle_id:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                # Освобождаем предыдущий транспорт водителя, если он был
                if driver.vehicle:
                    old_vehicle = driver.vehicle
                    old_vehicle.is_available = True
                    old_vehicle.save()
                
                # Назначаем новый транспорт
                vehicle.is_available = False
                vehicle.save()
                driver.vehicle = vehicle
            else:
                # Если транспорт не выбран, освобождаем текущий
                if driver.vehicle:
                    old_vehicle = driver.vehicle
                    old_vehicle.is_available = True
                    old_vehicle.save()
                driver.vehicle = None
            
            driver.save()
            messages.success(request, f'Транспорт для водителя {driver.user.get_full_name()} успешно обновлен')
        except (Driver.DoesNotExist, Vehicle.DoesNotExist):
            messages.error(request, 'Водитель или транспортное средство не найдены')
        return redirect('main:admin_drivers')

    return render(request, 'main/management/drivers.html', {
        'drivers': drivers,
        'available_vehicles': available_vehicles
    })

@staff_member_required
def news_list_admin(request):
    news = News.objects.all().order_by('-created_at')
    return render(request, 'main/admin/news_list.html', {'news': news})

@staff_member_required
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, 'Новость успешно создана!')
            return redirect('main:news_list_admin')
    else:
        form = NewsForm()
    return render(request, 'main/admin/news_form.html', {'form': form, 'action': 'Создать'})

@staff_member_required
def news_edit(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новость успешно обновлена!')
            return redirect('main:news_list_admin')
    else:
        form = NewsForm(instance=news)
    return render(request, 'main/admin/news_form.html', {'form': form, 'action': 'Редактировать'})

@staff_member_required
def news_delete(request, news_id):
    news_item = get_object_or_404(News, pk=news_id)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'Новость успешно удалена.')
        return redirect('main:news_list_admin') # Или куда вы хотите перенаправить после удаления
    return render(request, 'main/admin/news_delete_confirm.html', {'news_item': news_item})

def news_list(request):
    logger.info("Accessing news list page")
    all_news = News.objects.filter(is_published=True).order_by('-created_at')
    # TODO: Добавить пагинацию, если новостей много. Например, Django Paginator.
    # from django.core.paginator import Paginator
    # paginator = Paginator(all_news, 10) # По 10 новостей на страницу
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    # return render(request, 'main/news_list.html', {'page_obj': page_obj})
    # Пока просто передаем все новости
    return render(request, 'main/news.html', {'news_list': all_news})

def news_detail(request, news_id):
    news = get_object_or_404(News, id=news_id, is_published=True)
    other_news = News.objects.filter(is_published=True).exclude(id=news_id).order_by('-created_at')[:3]
    return render(request, 'main/news/detail.html', {
        'news': news,
        'other_news': other_news
    })
