from django.urls import path, include, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'insurance_app'  # Пространство имен для URL-адресов приложения

urlpatterns = [
    path('', views.home_page, name='home'),
    path('about/', views.company_info_page, name='company_info'),
    path('news/', views.news_list_page, name='news_list'),
    path('terms/', views.terms_dictionary_page, name='terms_dictionary'),
    path('contacts/', views.contacts_page, name='contacts'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('vacancies/', views.vacancies_page, name='vacancies'),
    path('reviews/', views.reviews_page, name='reviews'),
    path('promocodes/', views.promocodes_page, name='promocodes'),

    # CRUD для Отзывов
    path('my-reviews/', views.UserReviewListView.as_view(), name='user_reviews'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    # Публичные страницы для неавторизованных пользователей
    path('branches/', views.public_branches_list, name='public_branches'),
    path('insurance-types/', views.public_insurance_types_list, name='public_insurance_types'),

    # CRUD для Договоров (Contracts)
    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/create/', views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract_detail'),
    path('contracts/<int:pk>/update/', views.contract_update, name='contract_update'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),

    # Аутентификация
    path('login/', auth_views.LoginView.as_view(template_name='insurance_app/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Регистрация
    path('register/client/', views.register_client_view, name='register_client'),
    path('register/agent/', views.register_agent_view, name='register_agent'),

    # Заявки на страхование
    path('requests/', views.insurance_request_list, name='request_list'),
    path('requests/create/', views.insurance_request_create, name='request_create'),
    path('requests/<int:request_id>/assign/', views.assign_request_to_agent, name='assign_request'),

    # Профиль пользователя
    path('profile/', views.profile_view, name='profile'),

    # Панель Агента
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/profile/edit/', views.agent_profile_edit, name='agent_profile_edit'),
    path('agent/clients/', views.agent_clients_list, name='agent_clients_list'),

    # Отчеты для администратора
    path('reports/agent-income/', views.admin_agent_income_report, name='admin_agent_income_report'),
    path('reports/statistics/', views.admin_statistics_view, name='admin_statistics'),

    # Смена пароля
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='insurance_app/auth/password_change_form.html',
        success_url=reverse_lazy('insurance_app:password_change_done')
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='insurance_app/auth/password_change_done.html'
    ), name='password_change_done'),

    # Сброс пароля
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='insurance_app/auth/password_reset_form.html',
        email_template_name='insurance_app/auth/password_reset_email.html',
        subject_template_name='insurance_app/auth/password_reset_subject.txt',
        success_url=reverse_lazy('insurance_app:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='insurance_app/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='insurance_app/auth/password_reset_confirm.html',
        success_url=reverse_lazy('insurance_app:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='insurance_app/auth/password_reset_complete.html'
    ), name='password_reset_complete'),
] 