from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from . import views
from . import api_views

app_name = 'main'

router = DefaultRouter()
router.register(r'vehicle-types', api_views.VehicleTypeViewSet)
router.register(r'vehicles', api_views.VehicleViewSet)
router.register(r'drivers', api_views.DriverViewSet)
router.register(r'clients', api_views.ClientViewSet)
router.register(r'cargo-types', api_views.CargoTypeViewSet)
router.register(r'services', api_views.ServiceViewSet)
router.register(r'orders', api_views.OrderViewSet, basename='order')

urlpatterns = [
    # Основные страницы
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    path('dictionary/', views.dictionary, name='dictionary'),
    path('contacts/', views.contacts, name='contacts'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('promotions/', views.promotions, name='promotions'),
    path('statistics/', views.statistics, name='statistics'),
    
    # Поиск транспорта по номеру
    re_path(r'^vehicle/(?P<plate_number>[A-Z0-9]{1,2}\d{3}[A-Z]{2}\d{2,3})/$', 
            views.vehicle_detail_by_plate, name='vehicle_detail_by_plate'),
    
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    path('profile/driver/', views.driver_profile, name='driver_profile'),
    path('profile/client/', views.client_profile, name='client_profile'),
    
    path('driver/schedule/', views.driver_schedule, name='driver_schedule'),
    path('driver/clients/', views.driver_clients, name='driver_clients'),
    path('driver/cargo/', views.driver_cargo, name='driver_cargo'),
    path('driver/orders/', views.driver_orders, name='driver_orders'),
    path('driver/available-orders/', views.available_orders, name='available_orders'),
    path('driver/take-order/<int:order_id>/', views.take_order, name='take_order'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Клиентский функционал
    path('services/catalog/', views.service_catalog, name='service_catalog'),
    path('services/purchase/<int:service_id>/', views.purchase_service, name='purchase_service'),
    path('client/orders/', views.client_orders, name='client_orders'),
    path('client/promotions/', views.client_promotions, name='client_promotions'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<int:order_id>/review/', views.add_review, name='add_review'),
    path('order/<int:order_id>/apply-promotion/', views.apply_promotion, name='apply_promotion'),
    
    # Общая информация
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('drivers/list/', views.driver_list, name='driver_list'),
    path('drivers/delete/<int:driver_id>/', views.delete_driver, name='delete_driver'),
    path('services/categories/', views.service_categories, name='service_categories'),
    path('services/delete/<int:service_id>/', views.delete_service, name='delete_service'),
    path('services/additional/', views.additional_services, name='additional_services'),
    
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    
    # Timezone
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    
    # Административные маршруты
    path('management/orders/', views.admin_orders, name='admin_orders'),
    path('management/reviews/', views.admin_reviews, name='admin_reviews'),
    path('management/services/', views.admin_services, name='admin_services'),
    path('management/vehicles/', views.admin_vehicles, name='admin_vehicles'),
    path('management/drivers/', views.admin_drivers, name='admin_drivers'),
    
    # Новости
    path('news/', views.news_list, name='news_list'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('management/news/', views.news_list_admin, name='news_list_admin'),
    path('management/news/create/', views.news_create, name='news_create'),
    path('management/news/<int:news_id>/edit/', views.news_edit, name='news_edit'),
    path('management/news/<int:news_id>/delete/', views.news_delete, name='news_delete'),
] 