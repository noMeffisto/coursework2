from django.contrib import admin
from .models import (
    VehicleType, BodyType, Vehicle, Driver, Client,
    CargoType, Service, Order, Review, Promotion, Schedule, News,
    AboutPageContent, SiteSettings
)

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'type', 'body_type', 'plate_number', 'is_available')
    list_filter = ('type', 'body_type', 'is_available', 'year')
    search_fields = ('brand', 'model', 'plate_number')

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'experience', 'categories', 'vehicle')
    list_filter = ('experience', 'categories')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    raw_id_fields = ('user', 'vehicle')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'company_name')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone', 'company_name')
    raw_id_fields = ('user',)

@admin.register(CargoType)
class CargoTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_type', 'base_price', 'is_active')
    list_filter = ('vehicle_type', 'is_active')
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service', 'driver', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at', 'scheduled_date')
    search_fields = ('client__user__username', 'driver__user__username', 'pickup_address', 'delivery_address')
    raw_id_fields = ('client', 'driver', 'service', 'cargo_type')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'service', 'driver', 'status')
        }),
        ('Информация о грузе', {
            'fields': ('cargo_type', 'weight', 'volume')
        }),
        ('Адреса', {
            'fields': ('pickup_address', 'delivery_address')
        }),
        ('Расписание', {
            'fields': ('scheduled_date', 'scheduled_time')
        }),
        ('Стоимость', {
            'fields': ('total_price',)
        }),
        ('Дополнительно', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если это новый заказ
            if not obj.total_price:
                # Устанавливаем базовую цену из выбранной услуги
                obj.total_price = obj.service.base_price
        super().save_model(request, obj, form, change)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'text')

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'is_active', 'start_date', 'end_date', 'used_count')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('code', 'description')

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('driver', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('date', 'is_available')
    search_fields = ('driver__user__username', 'notes')
    raw_id_fields = ('driver',)

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at', 'author')
    search_fields = ('title', 'content')
    raw_id_fields = ('author',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(AboutPageContent)
class AboutPageContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_updated')
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        ('Наша миссия', {
            'fields': ('mission_title', 'mission_text'),
            'classes': ('collapse',)
        }),
        ('Наши ценности', {
            'fields': ('values_title', 'values_text'),
            'classes': ('collapse',)
        }),
    )
    # Запрещаем добавление новых объектов, если нужна только одна запись
    # def has_add_permission(self, request):
    #     return not AboutPageContent.objects.exists()

    # Запрещаем удаление, если нужна только одна запись
    # def has_delete_permission(self, request, obj=None):
    #     return False

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'contact_phone')

    def has_add_permission(self, request):
        # Разрешить добавление, только если еще нет ни одной записи
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запретить удаление настроек
        return False
