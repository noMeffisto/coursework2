from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Branch, InsuranceType, Agent, ClientProfile, Contract, Article,
    CompanyInfoSection, FAQ, StaffContact, Vacancy, Review, PromoCode,
    InsuranceRequest
)

# Inlines
class AgentInlineForUser(admin.StackedInline):
    model = Agent
    can_delete = False
    verbose_name_plural = 'Профиль страхового агента'
    fk_name = 'user'
    fields = ('first_name', 'last_name', 'patronymic', 'address', 'phone', 'branch', 'birth_date')
    min_num = 0
    max_num = 1

class ClientProfileInlineForUser(admin.StackedInline):
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Профиль клиента'
    fk_name = 'user'
    fields = ('birth_date', 'phone')
    min_num = 0
    max_num = 1

class AgentInlineForBranch(admin.TabularInline): # Или StackedInline
    model = Agent
    extra = 0 # Количество пустых форм для добавления
    fields = ('first_name', 'last_name', 'phone', 'birth_date')
    readonly_fields = ('first_name', 'last_name') # Если управление агентами идет отдельно
    show_change_link = True
    verbose_name_plural = 'Агенты в этом филиале'

class ContractInlineForClient(admin.TabularInline):
    model = Contract
    extra = 0
    fields = ('id', 'insurance_type', 'agent', 'branch', 'start_date', 'end_date', 'insurance_sum')
    readonly_fields = ('id', 'insurance_type', 'agent', 'branch', 'start_date', 'end_date', 'insurance_sum')
    show_change_link = True
    verbose_name_plural = 'Договоры клиента'
    def has_add_permission(self, request, obj=None):
        return False # Запрещаем добавление договоров из профиля клиента тут

class ContractInlineForAgent(admin.TabularInline):
    model = Contract
    fk_name = 'agent'
    extra = 0
    fields = ('id', 'client', 'insurance_type', 'branch', 'start_date', 'end_date', 'insurance_sum')
    readonly_fields = ('id', 'client', 'insurance_type', 'branch', 'start_date', 'end_date', 'insurance_sum')
    show_change_link = True
    verbose_name_plural = 'Заключенные договоры'
    def has_add_permission(self, request, obj=None):
        return False

# Custom User Admin
class UserAdmin(BaseUserAdmin):
    inlines = (AgentInlineForUser, ClientProfileInlineForUser)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_client_phone', 'get_agent_branch')
    list_select_related = ('agent_profile__branch', 'client_profile')

    def get_client_phone(self, instance):
        if hasattr(instance, 'client_profile') and instance.client_profile:
            return instance.client_profile.phone
        return "-"
    get_client_phone.short_description = 'Телефон клиента'

    def get_agent_branch(self, instance):
        if hasattr(instance, 'agent_profile') and instance.agent_profile and instance.agent_profile.branch:
            return instance.agent_profile.branch.name
        return "-"
    get_agent_branch.short_description = 'Филиал агента'

# ModelAdmins
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'image')
    search_fields = ('name', 'address')
    fields = ('name', 'address', 'phone', 'image')
    inlines = [AgentInlineForBranch]

@admin.register(InsuranceType)
class InsuranceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent_commission_percentage', 'description_short')
    search_fields = ('name', 'description')

    def description_short(self, obj):
        return obj.description[:75] + '...' if len(obj.description) > 75 else obj.description
    description_short.short_description = 'Краткое описание'

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('user_link','full_name', 'branch', 'phone', 'birth_date')
    search_fields = ('user__username', 'first_name', 'last_name', 'phone', 'branch__name')
    list_filter = ('branch', 'birth_date')
    list_select_related = ('user', 'branch')
    autocomplete_fields = ['user', 'branch']
    inlines = [ContractInlineForAgent]

    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name} {obj.patronymic or ''}".strip()
    full_name.short_description = 'Полное имя'
    
    def user_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.user:
            link = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return "-"
    user_link.short_description = 'Пользователь (логин)'


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'birth_date', 'phone')
    search_fields = ('user__username', 'phone')
    list_select_related = ('user',)
    autocomplete_fields = ['user']
    inlines = []
    
    def user_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'Пользователь (логин)'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('id','client_link', 'insurance_type', 'agent_link', 'branch', 'start_date', 'end_date', 'insurance_sum', 'tariff_rate', 'insurance_payment_display', 'created_at_formatted')
    list_filter = ('insurance_type', 'branch', 'agent', 'start_date', 'client')
    search_fields = ('client__user__username', 'client__user__first_name', 'client__user__last_name', 'agent__first_name', 'agent__last_name', 'insurance_type__name', 'id')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at', 'insurance_payment')
    list_select_related = ('client', 'insurance_type', 'agent', 'branch')
    autocomplete_fields = ['client', 'insurance_type', 'agent', 'branch']
    fieldsets = (
        (None, {
            'fields': ('client', 'insurance_type', 'agent', 'branch', 'insured_object_description')
        }),
        ('Финансовые условия', {
            'fields': ('insurance_sum', 'tariff_rate', 'insurance_payment')
        }),
        ('Сроки и даты', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
    )

    def insurance_payment_display(self, obj):
        return obj.insurance_payment
    insurance_payment_display.short_description = 'Страховой платеж'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    created_at_formatted.short_description = 'Создан (дата)'

    def client_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.client:
            # Ссылка на профиль пользователя, а не ClientProfile
            link = reverse("admin:auth_user_change", args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', link, obj.client.get_full_name() or obj.client.username)
        return "-"
    client_link.short_description = 'Клиент'

    def agent_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.agent:
            link = reverse("admin:insurance_app_agent_change", args=[obj.agent.id])
            return format_html('<a href="{}">{}</a>', link, obj.agent)
        return "-"
    agent_link.short_description = 'Агент'


@admin.register(InsuranceRequest)
class InsuranceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'insurance_type', 'status', 'assigned_agent', 'created_at')
    list_filter = ('status', 'insurance_type', 'created_at')
    search_fields = ('client__username', 'assigned_agent__last_name', 'insurance_type__name')
    list_select_related = ('client', 'insurance_type', 'assigned_agent')
    autocomplete_fields = ['client', 'insurance_type', 'assigned_agent']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ("Основная информация", {
            'fields': ('client', 'insurance_type', 'status', 'assigned_agent')
        }),
        ("Дополнительная информация", {
            'fields': ('client_notes', 'agent_notes')
        }),
        ("Даты", {
            'fields': ('created_at', 'updated_at')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'insurance_type', 'assigned_agent')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_content_display', 'published_at_formatted', 'created_at_formatted')
    list_filter = ('published_at',)
    search_fields = ('title', 'full_content')
    date_hierarchy = 'published_at'
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'short_content': ('title',)} # Пример, может не подойти для всех случаев

    def published_at_formatted(self, obj):
        return obj.published_at.strftime("%d/%m/%Y %H:%M")
    published_at_formatted.short_description = 'Опубликовано'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    created_at_formatted.short_description = 'Создано'

    def short_content_display(self, obj):
        return obj.short_content[:100] + '...' if len(obj.short_content) > 100 else obj.short_content
    short_content_display.short_description = 'Краткое содержание'

@admin.register(CompanyInfoSection)
class CompanyInfoSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_short')
    search_fields = ('title', 'content')

    def content_short(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_short.short_description = 'Содержание (начало)'

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_short', 'added_at_formatted')
    search_fields = ('question', 'answer')
    list_filter = ('added_at',)
    date_hierarchy = 'added_at'

    def answer_short(self, obj):
        return obj.answer[:100] + '...' if len(obj.answer) > 100 else obj.answer
    answer_short.short_description = 'Ответ (начало)'

    def added_at_formatted(self, obj):
        return obj.added_at.strftime("%d/%m/%Y %H:%M")
    added_at_formatted.short_description = 'Добавлено'

@admin.register(StaffContact)
class StaffContactAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'position', 'phone', 'email', 'birth_date')
    search_fields = ('last_name', 'first_name', 'position', 'email')
    list_filter = ('position', 'birth_date') # Добавлен фильтр по дате рождения

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'description_short', 'published_at_formatted')
    search_fields = ('title', 'description')
    list_filter = ('published_at',)
    date_hierarchy = 'published_at'

    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Описание (начало)'

    def published_at_formatted(self, obj):
        return obj.published_at.strftime("%d/%m/%Y %H:%M")
    published_at_formatted.short_description = 'Опубликовано'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'rating', 'text_short', 'created_at_formatted')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'text')
    date_hierarchy = 'created_at'
    list_select_related = ('user',)
    autocomplete_fields = ['user']

    def text_short(self, obj):
        return obj.text[:75] + '...' if len(obj.text) > 75 else obj.text
    text_short.short_description = 'Текст отзыва'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    created_at_formatted.short_description = 'Дата отзыва'

    def user_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', link, obj.user.username)
    user_link.short_description = 'Пользователь'


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description_short', 'discount_display', 'valid_from_formatted', 'valid_to_formatted', 'is_active', 'is_archived_display')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    filter_horizontal = ('applicable_insurance_types',) # Удобный виджет для ManyToMany
    fieldsets = (
        (None, {'fields': ('code', 'description', 'is_active')}),
        ('Условия скидки', {'fields': ('discount_percentage', 'discount_amount')}),
        ('Срок действия', {'fields': ('valid_from', 'valid_to')}),
        ('Применимость', {'fields': ('applicable_insurance_types',)})
    )

    def discount_display(self, obj):
        if obj.discount_percentage is not None:
            return f"{obj.discount_percentage}%"
        if obj.discount_amount is not None:
            return f"{obj.discount_amount} руб." # Предполагаем рубли
        return "-"
    discount_display.short_description = 'Скидка'

    def description_short(self, obj):
        return obj.description[:75] + '...' if len(obj.description) > 75 else obj.description
    description_short.short_description = 'Описание'

    def valid_from_formatted(self, obj):
        return obj.valid_from.strftime("%d/%m/%Y %H:%M") if obj.valid_from else "-"
    valid_from_formatted.short_description = 'Действ. с'

    def valid_to_formatted(self, obj):
        return obj.valid_to.strftime("%d/%m/%Y %H:%M") if obj.valid_to else "-"
    valid_to_formatted.short_description = 'Действ. до'
    
    def is_archived_display(self, obj):
        return "Да" if obj.is_archived else "Нет"
    is_archived_display.short_description = 'В архиве?'
    is_archived_display.boolean = True


# Перерегистрация стандартной модели User для добавления инлайнов
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Если какие-то модели не требуют сложной настройки, можно зарегистрировать их просто:
# admin.site.register(CompanyInfo) # Если бы была такая модель
# admin.site.register(PrivacyPolicyPage) # Если бы была такая модель

# Обратите внимание:
# 1. Для ImageField (Article, StaffContact) убедитесь, что Pillow установлен (`pip install Pillow`)
#    и настроены MEDIA_ROOT и MEDIA_URL в settings.py.
# 2. `autocomplete_fields` улучшают производительность для полей ForeignKey/ManyToManyField с большим количеством записей.
#    Для их работы нужно определить search_fields в админке связанной модели.
# 3. Для ClientProfile и Agent, которые связаны с User через OneToOneField, я добавил их как инлайны к UserAdmin.
#    Это позволяет редактировать профиль клиента или агента прямо на странице пользователя.
# 4. ФИО агента выводится как `full_name`.
# 5. Даты форматируются для лучшего отображения.
# 6. Добавлены ссылки на связанные объекты (например, на пользователя из отзыва или договора). 