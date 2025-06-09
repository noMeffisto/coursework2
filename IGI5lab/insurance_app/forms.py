from django import forms
from .models import Contract, Agent, Branch, InsuranceType, ClientProfile, InsuranceRequest, Review # Добавили ClientProfile, InsuranceRequest и Review
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator # Для телефона
import datetime # Для валидации возраста
from django.db import transaction

class ContractForm(forms.ModelForm):
    # Поля, которые должны быть выбираемыми (ForeignKey, ManyToManyField)
    # Если клиентов много, то для поля client лучше использовать CharField + JS виджет для поиска/выбора,
    # либо django-autocomplete-light. Пока оставим ModelChoiceField.
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(client_profile__isnull=False), # Только пользователи с профилем клиента
        label="Клиент",
        help_text="Выберите клиента, для которого оформляется договор.",
        required=True
    )
    insurance_type = forms.ModelChoiceField(
        queryset=InsuranceType.objects.all(),
        label="Вид страхования",
        empty_label=None, # Убрать пустой выбор, если вид страхования обязателен
        required=True
    )
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.all(),
        label="Страховой агент",
        required=False, # Агент может быть не указан сразу или его нет
        help_text="Выберите агента, оформляющего договор (необязательно)."
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        label="Филиал заключения",
        empty_label=None, # Филиал обязателен
        required=True
    )

    class Meta:
        model = Contract
        fields = [
            'client', 'insurance_type', 'agent', 'branch',
            'insured_object_description', 'insurance_sum', 'tariff_rate',
            'start_date', 'end_date'
        ]
        widgets = {
            'insured_object_description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'insurance_sum': forms.NumberInput(attrs={'step': '0.01'}),
            'tariff_rate': forms.NumberInput(attrs={'step': '0.0001'}),
        }
        labels = {
            'insured_object_description': 'Описание объекта страхования',
            'insurance_sum': 'Страховая сумма (руб.)',
            'tariff_rate': 'Тарифная ставка (например, 0.01 для 1%)',
            'start_date': 'Дата начала действия договора',
            'end_date': 'Дата окончания действия договора',
        }
        help_texts = {
            'tariff_rate': 'Указывается в долях единицы, например, 0.05 для 5%.',
            'insured_object_description': 'Например: автомобиль Lada Vesta, VIN XXXXXX; квартира по адресу ул. Мира, д.1, кв.1'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если нужно, можно здесь дополнительно настроить поля
        # Например, отфильтровать queryset для агентов в зависимости от выбранного филиала (потребует JS)
        self.fields['start_date'].input_formats = ('%Y-%m-%d',)
        self.fields['end_date'].input_formats = ('%Y-%m-%d',)

    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError("Дата окончания должна быть позже даты начала.")
        return end_date

    def clean_insurance_sum(self):
        insurance_sum = self.cleaned_data.get('insurance_sum')
        if insurance_sum is not None and insurance_sum <= 0:
            raise forms.ValidationError("Страховая сумма должна быть положительным числом.")
        return insurance_sum

    def clean_tariff_rate(self):
        tariff_rate = self.cleaned_data.get('tariff_rate')
        if tariff_rate is not None and (tariff_rate <= 0 or tariff_rate > 1):
            raise forms.ValidationError("Тарифная ставка должна быть в диапазоне (0, 1].")
        return tariff_rate


class ClientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Обязательное поле. Используется для уведомлений.')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=150, required=True, label='Фамилия')
    
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label='Дата рождения',
        help_text='Вам должно быть не менее 18 лет.'
    )
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', 
                                 message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = forms.CharField(validators=[phone_regex], max_length=20, label='Номер телефона', required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].input_formats = ('%Y-%m-%d',)

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Регистрация разрешена только для пользователей старше 18 лет.")
        return birth_date

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            ClientProfile.objects.create(
                user=user,
                birth_date=self.cleaned_data['birth_date'],
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class AgentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Обязательное поле. Используется для уведомлений.')
    first_name = forms.CharField(max_length=30, required=True, label='Имя')
    last_name = forms.CharField(max_length=150, required=True, label='Фамилия')
    patronymic = forms.CharField(max_length=100, required=False, label="Отчество")
    
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label='Дата рождения',
        help_text='Вам должно быть не менее 18 лет.'
    )
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', 
                                 message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = forms.CharField(validators=[phone_regex], max_length=20, label='Номер телефона')
    address = forms.CharField(max_length=300, label="Адрес")
    branch = forms.ModelChoiceField(queryset=Branch.objects.all(), label="Филиал")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].input_formats = ('%Y-%m-%d',)

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Регистрация разрешена только для сотрудников старше 18 лет.")
        return birth_date

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.is_staff = True # Агенты являются сотрудниками
        
        if commit:
            user.save()
            Agent.objects.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                patronymic=self.cleaned_data.get('patronymic', ''),
                address=self.cleaned_data['address'],
                phone=self.cleaned_data['phone'],
                branch=self.cleaned_data['branch'],
                birth_date=self.cleaned_data['birth_date']
            )
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True, help_text='Обязательное поле.')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Адрес электронной почты',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убедимся, что email остается обязательным, даже если в модели User он не strictly required
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверяем, не занят ли email другим пользователем, кроме текущего
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот адрес электронной почты уже используется другим пользователем.")
        return email


class ClientProfileUpdateForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label='Дата рождения',
        help_text='Вам должно быть не менее 18 лет.'
    )
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', 
                                 message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = forms.CharField(validators=[phone_regex], max_length=20, label='Номер телефона', required=False)

    class Meta:
        model = ClientProfile
        fields = ['birth_date', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].input_formats = ('%Y-%m-%d',)
        self.fields['birth_date'].required = True # Дата рождения обязательна для профиля

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Вам должно быть не менее 18 лет.")
        elif not birth_date: # Если поле не заполнено, но оно required
             raise forms.ValidationError("Это поле обязательно для заполнения.")
        return birth_date


class AgentProfileUpdateForm(forms.ModelForm):
    # first_name и last_name редактируются через UserUpdateForm для связанного User
    # email также редактируется через UserUpdateForm
    # branch, как правило, назначается администратором и не редактируется агентом напрямую

    patronymic = forms.CharField(max_length=100, required=False, label='Отчество')
    address = forms.CharField(max_length=300, required=True, label='Адрес') 
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', 
                                 message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = forms.CharField(validators=[phone_regex], max_length=20, label='Номер телефона', required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label='Дата рождения',
        help_text='Сотрудники должны быть старше 18 лет.',
        required=True
    )

    class Meta:
        model = Agent
        fields = ['patronymic', 'address', 'phone', 'birth_date'] # first_name, last_name убраны

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'].input_formats = ('%Y-%m-%d',)
        # Устанавливаем first_name и last_name из связанного User, если они есть в Agent модели
        # Это если мы решим оставить дублирующие поля в Agent. Пока что они убраны из fields.
        # if self.instance and self.instance.user:
        #     self.fields['first_name'].initial = self.instance.user.first_name
        #     self.fields['last_name'].initial = self.instance.user.last_name

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = datetime.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                raise forms.ValidationError("Сотрудники должны быть старше 18 лет.")
        elif not birth_date:
             raise forms.ValidationError("Это поле обязательно для заполнения.")
        return birth_date
    
    # Если first_name и last_name остаются в Agent и должны синхронизироваться с User:
    # def save(self, commit=True):
    #     agent_instance = super().save(commit=False)
    #     if agent_instance.user:
    #         # Если мы хотим, чтобы изменения first_name/last_name в этой форме
    #         # обновляли и User модель (что не очень хорошо, т.к. UserUpdateForm за это отвечает)
    #         # То здесь нужно добавить логику обновления user.first_name, user.last_name
    #         # user = agent_instance.user
    #         # user.first_name = self.cleaned_data.get('first_name', user.first_name)
    #         # user.last_name = self.cleaned_data.get('last_name', user.last_name)
    #         # if commit: user.save()
    #         pass # Пока не делаем этого
    #     if commit:
    #         agent_instance.save()
    #     return agent_instance


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
        labels = {
            'rating': 'Ваша оценка (от 1 до 5)',
            'text': 'Текст отзыва',
        }
        help_texts = {
            'text': 'Поделитесь вашими впечатлениями о работе с нашей компанией.'
        }


class InsuranceRequestForm(forms.ModelForm):
    class Meta:
        model = InsuranceRequest
        fields = ['insurance_type', 'client_notes']
        widgets = {
            'client_notes': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'insurance_type': 'Выберите вид страхования',
            'client_notes': 'Ваши пожелания или вопросы (необязательно)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если нужно, можно здесь дополнительно настроить поля
        # Например, отфильтровать queryset для видов страхования
        self.fields['insurance_type'].queryset = InsuranceType.objects.all()
        self.fields['insurance_type'].empty_label = None # Убрать пустой выбор, если вид страхования обязателен
        self.fields['insurance_type'].required = True

    #     return agent_instance 