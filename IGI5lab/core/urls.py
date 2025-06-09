from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
] 