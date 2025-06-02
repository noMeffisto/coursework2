from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from .models import Order, Service, VehicleType, Review, Driver, Client, News
from django.db import transaction
from decimal import Decimal

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, label='Имя')
    last_name = forms.CharField(max_length=30, label='Фамилия')
    phone = forms.CharField(max_length=20, label='Телефон')
    address = forms.CharField(max_length=500, label='Адрес', required=False)
    
    is_driver = forms.BooleanField(label='Я водитель', required=False)
    
    experience = forms.IntegerField(label='Опыт вождения (лет)', required=False, min_value=0)
    categories = forms.CharField(label='Категории прав (через запятую, например: B,C)', max_length=50, required=False)
    photo = forms.ImageField(label='Фотография профиля', required=False)
    birth_date = forms.DateField(label='Дата рождения (ДД.ММ.ГГГГ)', required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    company_name = forms.CharField(label='Название компании (если есть)', max_length=200, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean(self):
        cleaned_data = super().clean()
        is_driver = cleaned_data.get('is_driver')
        
        if is_driver:
            experience = cleaned_data.get('experience')
            categories = cleaned_data.get('categories')
            birth_date = cleaned_data.get('birth_date')
            
            if experience is None:
                self.add_error('experience', 'Водителю необходимо указать опыт работы.')
            if not categories:
                self.add_error('categories', 'Водителю необходимо указать категории прав.')
            if not birth_date:
                self.add_error('birth_date', 'Водителю необходимо указать дату рождения.')
            elif birth_date:
                # Проверка возраста
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                if age < 18:
                    self.add_error('birth_date', 'Водитель должен быть старше 18 лет.')
                # Проверка опыта относительно возраста
                if experience and age < (18 + experience):
                    self.add_error('experience', f'Указанный опыт невозможен. Для опыта {experience} лет минимальный возраст должен быть {18 + experience} лет.')
        else:
            address = cleaned_data.get('address')
            if not address:
                self.add_error('address', 'Клиенту необходимо указать адрес.')
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()

        is_driver = self.cleaned_data.get('is_driver')
        if is_driver:
            Driver.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                experience=self.cleaned_data['experience'],
                categories=self.cleaned_data['categories'],
                photo=self.cleaned_data.get('photo'),
                birth_date=self.cleaned_data['birth_date']
            )
        else:
            Client.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                company_name=self.cleaned_data.get('company_name')
            )
        return user

class ServiceFilterForm(forms.Form):
    min_price = forms.DecimalField(required=False, label='Минимальная цена')
    max_price = forms.DecimalField(required=False, label='Максимальная цена')
    vehicle_type = forms.ChoiceField(required=False, label='Тип транспорта')
    is_active = forms.BooleanField(required=False, label='Только активные')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle_type'].choices = [('', '---')] + [(vt.id, str(vt)) for vt in VehicleType.objects.all()]

class OrderForm(forms.ModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата доставки'
    )

    def __init__(self, *args, service=None, **kwargs):
        self.service = service
        super().__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ['cargo_type', 'pickup_address', 'delivery_address', 'weight', 'volume', 'notes', 'scheduled_date']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'pickup_address': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0'}),
            'cargo_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        weight = cleaned_data.get('weight')
        volume = cleaned_data.get('volume')
        scheduled_date = cleaned_data.get('scheduled_date')

        if self.service and weight and volume:
            if weight > self.service.max_weight:
                raise forms.ValidationError('Вес груза превышает максимально допустимый для данной услуги')
            if volume > self.service.max_volume:
                raise forms.ValidationError('Объем груза превышает максимально допустимый для данной услуги')

        if scheduled_date and scheduled_date < timezone.now().date():
            raise forms.ValidationError('Дата доставки не может быть в прошлом')

        return cleaned_data

    def save(self, commit=True):
        order = super().save(commit=False)
        if self.service:
            order.service = self.service
        if not order.total_price:  # Calculate price only if not already set
            base_price = self.service.base_price
            weight_factor = Decimal(str(order.weight)) / Decimal(str(self.service.max_weight))
            volume_factor = Decimal(str(order.volume)) / Decimal(str(self.service.max_volume))
            factor = max(weight_factor, volume_factor)
            order.total_price = base_price * (Decimal('1') + factor * Decimal('0.5'))
        
        if commit:
            order.save()
        return order

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)])
        }

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        } 