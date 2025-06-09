from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Article, CompanyInfoSection, FAQ, StaffContact, Vacancy, Review, PromoCode, Branch, InsuranceType, Contract, Agent, ClientProfile, InsuranceRequest
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import ContractForm, ClientRegistrationForm, AgentRegistrationForm, UserUpdateForm, ClientProfileUpdateForm, AgentProfileUpdateForm, InsuranceRequestForm, ReviewForm
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal
import json
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
import requests
import datetime

# Главная страница
def home_page(request):
    latest_article = Article.objects.filter(published_at__lte=timezone.now()).order_by('-published_at').first()
    context = {
        'latest_article': latest_article,
        'page_title': 'Главная страница'
    }
    return render(request, 'insurance_app/home.html', context)

# О компании
def company_info_page(request):
    sections = CompanyInfoSection.objects.all().order_by('id') # Добавим сортировку для предсказуемости
    context = {
        'sections': sections,
        'page_title': 'О нашей компании'
    }
    return render(request, 'insurance_app/company_info.html', context)

# Новости (список статей)
def news_list_page(request):
    articles = Article.objects.filter(published_at__lte=timezone.now()).order_by('-published_at')
    context = {
        'articles': articles,
        'page_title': 'Все новости'
    }
    return render(request, 'insurance_app/news_list.html', context)

# Словарь терминов и понятий (FAQ)
def terms_dictionary_page(request):
    faqs = FAQ.objects.order_by('-added_at')
    context = {
        'faqs': faqs,
        'page_title': 'Словарь терминов и понятий (FAQ)'
    }
    return render(request, 'insurance_app/terms_dictionary.html', context)

# Контакты
def contacts_page(request):
    staff_contacts = StaffContact.objects.all().order_by('last_name', 'first_name')
    context = {
        'staff_contacts': staff_contacts,
        'page_title': 'Свяжитесь с нами'
    }
    return render(request, 'insurance_app/contacts.html', context)

# Политика конфиденциальности
def privacy_policy(request):
    quote = "Не удалось получить цитату."
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                q = data[0].get('q', '')
                a = data[0].get('a', '')
                if q and a:
                    quote = f"{q} — {a}"
                elif q:
                    quote = q
    except Exception:
        pass

    weather = "Не удалось получить погоду."
    try:
        resp = requests.get('https://wttr.in/Шклов?format=3', timeout=7)
        if resp.status_code == 200 and resp.text.strip():
            weather = resp.text.strip()
    except Exception:
        pass

    now = timezone.localtime(timezone.now())
    now_utc = timezone.now().astimezone(datetime.timezone.utc)
    now_utc_minus3 = now_utc - datetime.timedelta(hours=3)
    return render(request, 'insurance_app/privacy_policy.html', {
        'quote': quote,
        'weather': weather,
        'now': now,
        'now_utc': now_utc,
        'now_utc_minus3': now_utc_minus3,
        'TIME_ZONE': timezone.get_current_timezone_name(),
    })

# Вакансии
def vacancies_page(request):
    vacancies = Vacancy.objects.filter(published_at__lte=timezone.now()).order_by('-published_at')
    context = {
        'vacancies': vacancies,
        'page_title': 'Карьера у нас'
    }
    return render(request, 'insurance_app/vacancies.html', context)

# Отзывы
def reviews_page(request):
    reviews = Review.objects.select_related('user').order_by('-created_at')
    context = {
        'reviews': reviews,
        'page_title': 'Отзывы наших клиентов'
    }
    return render(request, 'insurance_app/reviews.html', context)

# Промокоды и купоны
def promocodes_page(request):
    now = timezone.now()
    active_promocodes = PromoCode.objects.filter(is_active=True, valid_from__lte=now, valid_to__gte=now).prefetch_related('applicable_insurance_types')
    archived_promocodes = PromoCode.objects.filter(is_active=False) | \
                        PromoCode.objects.filter(valid_to__lt=now)
    archived_promocodes = archived_promocodes.distinct().prefetch_related('applicable_insurance_types')

    context = {
        'active_promocodes': active_promocodes,
        'archived_promocodes': archived_promocodes,
        'page_title': 'Наши промокоды и купоны'
    }
    return render(request, 'insurance_app/promocodes.html', context)

# Страницы для отображения информации для неавторизованного пользователя
def public_branches_list(request):
    branches = Branch.objects.all().order_by('name')
    context = {
        'branches': branches,
        'page_title': 'Наши филиалы по всей стране'
    }
    return render(request, 'insurance_app/public_branches.html', context)

def public_insurance_types_list(request):
    insurance_types = InsuranceType.objects.all().order_by('name')
    context = {
        'insurance_types': insurance_types,
        'page_title': 'Наши предложения по страхованию'
    }
    return render(request, 'insurance_app/public_insurance_types.html', context)

# --- CRUD для Отзывов (Review) ---

# Read (List)
class UserReviewListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Review
    template_name = 'insurance_app/reviews/user_review_list.html'
    context_object_name = 'reviews'
    paginate_by = 5

    def test_func(self):
        # Доступ только для клиентов
        return hasattr(self.request.user, 'client_profile')

    def get_queryset(self):
        # Показываем отзывы только текущего пользователя
        return Review.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Мои отзывы'
        return context

# Create
class ReviewCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'insurance_app/reviews/review_form.html'
    success_url = reverse_lazy('insurance_app:user_reviews')

    def test_func(self):
        # Доступ только для клиентов
        return hasattr(self.request.user, 'client_profile')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Ваш отзыв был успешно опубликован!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Оставить новый отзыв'
        return context

# Update
class ReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'insurance_app/reviews/review_form.html'
    success_url = reverse_lazy('insurance_app:user_reviews')
    
    def test_func(self):
        review = self.get_object()
        return self.request.user == review.user

    def form_valid(self, form):
        messages.success(self.request, "Ваш отзыв был успешно обновлен.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Редактировать отзыв'
        return context

# Delete
class ReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'insurance_app/reviews/review_confirm_delete.html'
    success_url = reverse_lazy('insurance_app:user_reviews')
    
    def test_func(self):
        review = self.get_object()
        return self.request.user == review.user
    
    def form_valid(self, form):
        messages.success(self.request, "Ваш отзыв был успешно удален.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Подтвердить удаление отзыва'
        return context

# --- CRUD для Договоров (Contract) ---

# Read (List)
class ContractListView(ListView):
    model = Contract
    template_name = 'insurance_app/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Contract.objects.all().select_related('client', 'insurance_type', 'agent', 'branch').order_by('-start_date')
        elif hasattr(self.request.user, 'agent_profile') and self.request.user.agent_profile:
            return Contract.objects.filter(agent=self.request.user.agent_profile).select_related('client', 'insurance_type', 'branch').order_by('-start_date')
        elif hasattr(self.request.user, 'client_profile') and self.request.user.client_profile:
            return Contract.objects.filter(client=self.request.user).select_related('insurance_type', 'agent', 'branch').order_by('-start_date')
        return Contract.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Список договоров страхования'
        return context

# Read (Detail)
class ContractDetailView(DetailView):
    model = Contract
    template_name = 'insurance_app/contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        qs = super().get_queryset().select_related('client', 'insurance_type', 'agent', 'branch')
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return qs
            if hasattr(self.request.user, 'agent_profile') and self.request.user.agent_profile:
                return qs.filter(agent=self.request.user.agent_profile)
            if hasattr(self.request.user, 'client_profile') and self.request.user.client_profile:
                return qs.filter(client=self.request.user)
        return qs.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
             context['page_title'] = f"Договор №{self.object.id}"
        else:
             context['page_title'] = "Детали договора"
        return context

# Create
@login_required
def contract_create(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'agent_profile') and request.user.agent_profile)):
        messages.error(request, "У вас нет прав на создание договоров.")
        return redirect('insurance_app:home')

    if request.method == 'POST':
        form = ContractForm(request.POST)
        if form.is_valid():
            contract = form.save(commit=False)
            if hasattr(request.user, 'agent_profile') and request.user.agent_profile and not form.cleaned_data.get('agent'):
                 contract.agent = request.user.agent_profile
            contract.save()
            messages.success(request, f"Договор №{contract.id} успешно создан.")
            return redirect('insurance_app:contract_detail', pk=contract.pk)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ContractForm()
        if hasattr(request.user, 'agent_profile') and request.user.agent_profile:
            form.fields['agent'].initial = request.user.agent_profile

    context = {
        'form': form,
        'page_title': 'Оформление нового договора страхования'
    }
    return render(request, 'insurance_app/contract_form.html', context)

# Update
@login_required
def contract_update(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not (request.user.is_superuser or 
            (hasattr(request.user, 'agent_profile') and request.user.agent_profile and contract.agent == request.user.agent_profile)):
        messages.error(request, "У вас нет прав на редактирование этого договора.")
        return redirect('insurance_app:contract_detail', pk=contract.pk)

    if request.method == 'POST':
        form = ContractForm(request.POST, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, f"Договор №{contract.id} успешно обновлен.")
            return redirect('insurance_app:contract_detail', pk=contract.pk)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
    else:
        form = ContractForm(instance=contract)

    context = {
        'form': form,
        'contract': contract, 
        'page_title': f'Редактирование договора №{contract.id}'
    }
    return render(request, 'insurance_app/contract_form.html', context)

# Delete
@login_required
def contract_delete(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not request.user.is_superuser:
        messages.error(request, "У вас нет прав на удаление договоров.")
        return redirect('insurance_app:contract_detail', pk=contract.pk)

    if request.method == 'POST':
        contract_id = contract.id
        contract.delete()
        messages.success(request, f"Договор №{contract_id} успешно удален.")
        return redirect('insurance_app:contract_list')

    context = {
        'contract': contract,
        'page_title': f'Удаление договора №{contract.id}'
    }
    return render(request, 'insurance_app/contract_confirm_delete.html', context)

# --- Прочие пользовательские страницы ---

# Регистрация
def register_client_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Вы уже вошли в систему.")
        return redirect('insurance_app:home')

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно! Добро пожаловать!")
            return redirect('insurance_app:home')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме регистрации.")
    else:
        form = ClientRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Регистрация нового клиента'
    }
    return render(request, 'insurance_app/auth/register_client.html', context)

def register_agent_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Вы уже вошли в систему.")
        return redirect('insurance_app:home')

    if request.method == 'POST':
        form = AgentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация агента прошла успешно! Ваш профиль создан.")
            return redirect('insurance_app:agent_dashboard')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме регистрации.")
    else:
        form = AgentRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Регистрация нового агента'
    }
    return render(request, 'insurance_app/auth/register_agent.html', context)

# Профиль клиента
@login_required
@transaction.atomic
def profile_view(request):
    try:
        client_profile = request.user.client_profile
    except ClientProfile.DoesNotExist:
        # Этого не должно происходить, если регистрация работает правильно,
        # но на всякий случай создадим профиль, если его нет.
        client_profile = ClientProfile.objects.create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ClientProfileUpdateForm(request.POST, instance=client_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('insurance_app:profile')  # Перенаправляем на ту же страницу
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ClientProfileUpdateForm(instance=client_profile)

    # Получаем последние отзывы пользователя
    user_reviews = Review.objects.filter(user=request.user).order_by('-created_at')[:3]

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_reviews': user_reviews,
        'page_title': 'Мой профиль'
    }
    return render(request, 'insurance_app/auth/profile.html', context) 

# --- Функционал для агентов ---

# Панель агента
@login_required
def agent_dashboard(request):
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        messages.error(request, "Эта страница доступна только для страховых агентов.")
        return redirect('insurance_app:home')

    agent = request.user.agent_profile
    latest_contracts = Contract.objects.filter(agent=agent).order_by('-created_at')[:5]
    
    # Новые заявки для агента
    pending_requests = InsuranceRequest.objects.filter(status='pending').select_related('client', 'insurance_type')
    my_assigned_requests = InsuranceRequest.objects.filter(assigned_agent=agent, status__in=['assigned', 'processing']).select_related('client', 'insurance_type')

    context = {
        'page_title': 'Панель страхового агента',
        'agent': agent,
        'latest_contracts': latest_contracts,
        'pending_requests': pending_requests,
        'my_assigned_requests': my_assigned_requests,
    }
    return render(request, 'insurance_app/agent/agent_dashboard.html', context)

# Редактирование профиля агента
@login_required
@transaction.atomic
def agent_profile_edit(request):
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        messages.error(request, "Эта функция доступна только для страховых агентов.")
        return redirect('insurance_app:home')

    agent_profile = request.user.agent_profile
    user_instance = request.user

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user_instance)
        agent_form = AgentProfileUpdateForm(request.POST, instance=agent_profile)

        if user_form.is_valid() and agent_form.is_valid():
            # Обновляем поля first_name и last_name в модели Agent из данных User
            # Это необходимо, если мы хотим, чтобы Agent.first_name и Agent.last_name были актуальны
            # и отображались, например, в админке Agent или где-то еще.
            # Однако, если эти поля в Agent - просто для отображения и не являются "источником правды",
            # то эту синхронизацию можно делать по-другому или не делать вообще.
            # Пока что мы оставили их в модели Agent.

            updated_user = user_form.save(commit=False) # Получаем обновленного пользователя
            agent_instance = agent_form.save(commit=False) # Получаем обновленного агента
            
            # Синхронизируем first_name, last_name из User в Agent
            agent_instance.first_name = updated_user.first_name
            agent_instance.last_name = updated_user.last_name
            
            updated_user.save() # Сохраняем пользователя
            agent_instance.save() # Сохраняем агента

            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('insurance_app:agent_dashboard') 
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserUpdateForm(instance=user_instance)
        agent_form = AgentProfileUpdateForm(instance=agent_profile)
    
    context = {
        'user_form': user_form,
        'agent_form': agent_form,
        'page_title': 'Редактировать профиль агента'
    }
    return render(request, 'insurance_app/agent/agent_profile_form.html', context)

@login_required
def agent_clients_list(request):
    if not hasattr(request.user, 'agent_profile') or not request.user.agent_profile:
        messages.error(request, "Эта функция доступна только для страховых агентов.")
        return redirect('insurance_app:home')

    agent = request.user.agent_profile
    # Получаем ID всех клиентов, с которыми у агента есть договоры
    client_ids = Contract.objects.filter(agent=agent).values_list('client_id', flat=True).distinct()
    # Получаем объекты User для этих клиентов
    clients_users = User.objects.filter(id__in=client_ids).select_related('client_profile').order_by('last_name', 'first_name')

    context = {
        'page_title': 'Мои клиенты',
        'clients': clients_users,
    }
    return render(request, 'insurance_app/agent/agent_clients_list.html', context)

@staff_member_required
def admin_agent_income_report(request):
    contracts = Contract.objects.select_related(
        'agent', 'agent__branch', 'insurance_type', 'client'
    ).filter(agent__isnull=False).order_by('agent__branch__name', 'agent__last_name', 'agent__first_name', '-created_at')

    report_data = []
    total_commission_overall = Decimal('0.00')

    for contract in contracts:
        insurance_payment = contract.insurance_payment # Используем свойство
        agent_commission_percentage = contract.insurance_type.agent_commission_percentage
        agent_commission_amount = (insurance_payment * agent_commission_percentage) / Decimal('100.0')
        total_commission_overall += agent_commission_amount

        report_data.append({
            'contract_id': contract.id,
            'branch_name': contract.agent.branch.name if contract.agent.branch else 'N/A',
            'agent_name': contract.agent.get_full_name_display() if contract.agent else 'N/A',
            'client_name': contract.client.get_full_name() if contract.client else contract.client.username,
            'insurance_type_name': contract.insurance_type.name,
            'insurance_sum': contract.insurance_sum,
            'tariff_rate': contract.tariff_rate,
            'insurance_payment': insurance_payment,
            'agent_commission_percentage': agent_commission_percentage,
            'agent_commission_amount': agent_commission_amount.quantize(Decimal('0.01')),
            'contract_start_date': contract.start_date,
            'contract_created_at': contract.created_at,
        })

    context = {
        'page_title': 'Отчет: Доход агентов',
        'report_data': report_data,
        'total_commission_overall': total_commission_overall.quantize(Decimal('0.01')),
    }
    return render(request, 'insurance_app/admin_reports/agent_income_report.html', context)

@staff_member_required
def admin_statistics_view(request):
    # 1. Contracts per month (last 12 months)
    contracts_by_month = (
        Contract.objects
        .annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # 2. Contracts by insurance type
    contracts_by_type = (
        Contract.objects
        .values('insurance_type__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # 3. Contracts by branch
    contracts_by_branch = (
        Contract.objects
        .values('branch__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # 4. Insurance sum per month
    sum_by_month = (
        Contract.objects
        .annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(total_sum=Sum('insurance_sum'))
        .order_by('month')
    )

    # Prepare data for Chart.js
    contracts_by_month_data = {
        "labels": [c['month'].strftime("%b %Y") for c in contracts_by_month],
        "data": [c['count'] for c in contracts_by_month],
    }
    
    contracts_by_type_data = {
        "labels": [c['insurance_type__name'] for c in contracts_by_type],
        "data": [c['count'] for c in contracts_by_type],
    }

    contracts_by_branch_data = {
        "labels": [c['branch__name'] for c in contracts_by_branch],
        "data": [c['count'] for c in contracts_by_branch],
    }

    sum_by_month_data = {
        "labels": [s['month'].strftime("%b %Y") for s in sum_by_month],
        "data": [float(s['total_sum']) for s in sum_by_month],
    }

    context = {
        'page_title': 'Статистика и аналитика',
        'contracts_by_month_json': json.dumps(contracts_by_month_data),
        'contracts_by_type_json': json.dumps(contracts_by_type_data),
        'contracts_by_branch_json': json.dumps(contracts_by_branch_data),
        'sum_by_month_json': json.dumps(sum_by_month_data),
    }
    return render(request, 'insurance_app/admin_reports/statistics.html', context)

# --- Заявки на страхование ---

# Список заявок клиента
@login_required
def insurance_request_list(request):
    if not hasattr(request.user, 'client_profile'):
        messages.error(request, "Эта страница доступна только для клиентов.")
        return redirect('insurance_app:home')
    
    requests = InsuranceRequest.objects.filter(client=request.user).select_related('insurance_type', 'assigned_agent').order_by('-created_at')
    context = {
        'requests': requests,
        'page_title': 'Мои заявки на страхование'
    }
    return render(request, 'insurance_app/requests/request_list.html', context)

# Создание заявки клиентом
@login_required
def insurance_request_create(request):
    if not hasattr(request.user, 'client_profile'):
        messages.error(request, "Только клиенты могут создавать заявки.")
        return redirect('insurance_app:home')

    if request.method == 'POST':
        form = InsuranceRequestForm(request.POST)
        if form.is_valid():
            request_instance = form.save(commit=False)
            request_instance.client = request.user
            request_instance.save()
            messages.success(request, "Ваша заявка успешно отправлена! Агент свяжется с вами в ближайшее время.")
            return redirect('insurance_app:request_list')
    else:
        form = InsuranceRequestForm()

    context = {
        'form': form,
        'page_title': 'Создать заявку на страхование'
    }
    return render(request, 'insurance_app/requests/request_form.html', context)

# Назначение заявки агенту
@login_required
def assign_request_to_agent(request, request_id):
    if not hasattr(request.user, 'agent_profile'):
        messages.error(request, "Только агенты могут брать заявки в работу.")
        return redirect('insurance_app:home')

    if request.method == 'POST':
        insurance_request = get_object_or_404(InsuranceRequest, id=request_id, status='pending')
        insurance_request.assigned_agent = request.user.agent_profile
        insurance_request.status = 'assigned'
        insurance_request.save()
        messages.success(request, f"Заявка №{insurance_request.id} успешно взята в работу.")
    else:
        messages.warning(request, "Неверный метод запроса.")
    
    return redirect('insurance_app:agent_dashboard')
