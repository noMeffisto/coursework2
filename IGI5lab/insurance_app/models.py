from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название филиала")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = models.CharField(validators=[phone_regex], max_length=20, verbose_name="Телефон")
    image = models.ImageField(upload_to='branch_photos/', blank=True, null=True, verbose_name="Фото филиала")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

class InsuranceType(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название вида страхования")
    description = models.TextField(verbose_name="Описание")
    agent_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Процент комиссии агенту")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Вид страхования"
        verbose_name_plural = "Виды страхования"

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="agent_profile", null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    address = models.CharField(max_length=300, verbose_name="Адрес")
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = models.CharField(validators=[phone_regex], max_length=20, verbose_name="Телефон")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, verbose_name="Филиал")
    # Предполагаем, что у агентов тоже есть возрастное ограничение
    birth_date = models.DateField(verbose_name="Дата рождения", help_text="Сотрудники должны быть старше 18 лет.")

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = "Страховой агент"
        verbose_name_plural = "Страховые агенты"

# Для клиентов можно использовать встроенную модель User или расширить ее
# Если клиенты регистрируются, User модель подходит.
# Если нужны доп. поля для клиентов, не являющихся агентами или сотрудниками:
class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name="client_profile")
    # Пример дополнительных полей для клиента
    birth_date = models.DateField(verbose_name="Дата рождения", help_text="Клиенты должны быть старше 18 лет.", null=True, blank=True)
    phone_regex = RegexValidator(regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$', message="Номер телефона должен быть в формате: +375 (XX) XXX-XX-XX")
    phone = models.CharField(validators=[phone_regex], max_length=20, verbose_name="Телефон", blank=True, null=True)
    # Можно добавить другие поля, специфичные для клиента

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"


class Contract(models.Model):
    client = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Клиент", related_name="contracts") # Используем User, предполагая регистрацию клиентов
    insurance_type = models.ForeignKey(InsuranceType, on_delete=models.PROTECT, verbose_name="Вид страхования")
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Страховой агент")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, verbose_name="Филиал заключения")
    insured_object_description = models.TextField(verbose_name="Описание объекта страхования", blank=True, help_text="Например, автомобиль (марка, модель, VIN), квартира (адрес) и т.д.")
    insurance_sum = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Страховая сумма")
    tariff_rate = models.DecimalField(max_digits=5, decimal_places=4, validators=[MinValueValidator(0)], verbose_name="Тарифная ставка (например, 0.01 для 1%)")
    start_date = models.DateField(verbose_name="Дата заключения (начала действия)")
    end_date = models.DateField(verbose_name="Дата окончания действия")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления записи")

    @property
    def insurance_payment(self):
        if self.insurance_sum is not None and self.tariff_rate is not None:
            return self.insurance_sum * self.tariff_rate
        return 0

    def __str__(self):
        return f"Договор №{self.id} от {self.start_date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Договор о страховании"
        verbose_name_plural = "Договоры о страховании"
        ordering = ['-start_date']

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    short_content = models.CharField(max_length=255, verbose_name="Краткое содержание")
    full_content = models.TextField(verbose_name="Полное содержание")
    image = models.ImageField(upload_to='articles_images/', blank=True, null=True, verbose_name="Картинка")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления записи")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Статья (Новость)"
        verbose_name_plural = "Статьи (Новости)"
        ordering = ['-published_at']

class CompanyInfoSection(models.Model):
    """Разделы для страницы 'О компании', например, история, реквизиты"""
    title = models.CharField(max_length=200, verbose_name="Заголовок раздела")
    content = models.TextField(verbose_name="Содержание")
    # Можно добавить поле для порядка отображения, если нужно
    # order = models.PositiveIntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Раздел 'О компании'"
        verbose_name_plural = "Разделы 'О компании'"
        # ordering = ['order']

class FAQ(models.Model):
    question = models.CharField(max_length=300, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    added_at = models.DateTimeField(default=timezone.now, verbose_name="Дата добавления")

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Вопрос-ответ (FAQ)"
        verbose_name_plural = "Вопросы-ответы (FAQ)"
        ordering = ['-added_at']

class StaffContact(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    position = models.CharField(max_length=150, verbose_name="Должность/Описание работ")
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True, verbose_name="Фото")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Электронная почта")
    birth_date = models.DateField(verbose_name="Дата рождения", help_text="Сотрудники должны быть старше 18 лет.", null=True, blank=True) # Добавлено поле для возраста

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.position}"

    class Meta:
        verbose_name = "Контакт сотрудника"
        verbose_name_plural = "Контакты сотрудников"

class Vacancy(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название вакансии")
    description = models.TextField(verbose_name="Описание")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="Дата публикации")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-published_at']

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь (клиент)") # Отзыв оставляет зарегистрированный пользователь
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Оценка")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата отзыва")

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.rating}/5"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Промокод")
    description = models.TextField(blank=True, verbose_name="Описание")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Процент скидки", null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Сумма скидки", null=True, blank=True)
    valid_from = models.DateTimeField(verbose_name="Действителен с")
    valid_to = models.DateTimeField(verbose_name="Действителен до")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    # Связь многие ко многим с видами страхования, если промокод применяется к конкретным видам
    applicable_insurance_types = models.ManyToManyField(InsuranceType, blank=True, verbose_name="Применим к видам страхования")

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Промокод/Купон"
        verbose_name_plural = "Промокоды и купоны"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.discount_percentage is None and self.discount_amount is None:
            raise ValidationError("Укажите либо процент скидки, либо сумму скидки.")
        if self.discount_percentage is not None and self.discount_amount is not None:
            raise ValidationError("Укажите либо процент скидки, либо сумму скидки, но не оба вместе.")
        if self.valid_to <= self.valid_from:
            raise ValidationError("Дата окончания действия должна быть позже даты начала.")

    @property
    def is_archived(self):
        return not self.is_active and self.valid_to < timezone.now()

# Для полноты картины, добавим модель для объектов страхования, если они сложнее чем просто описание в договоре
# class InsuredObject(models.Model):
#     name = models.CharField(max_length=200, verbose_name="Наименование объекта")
#     description = models.TextField(verbose_name="Подробное описание")
#     # Связь с клиентом, если нужно хранить объекты отдельно от договоров
#     owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="insured_objects", verbose_name="Владелец")
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Объект страхования"
#         verbose_name_plural = "Объекты страхования"

class InsuranceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает рассмотрения'),
        ('assigned', 'Назначена агенту'),
        ('processing', 'В обработке'),
        ('completed', 'Завершено (договор создан)'),
        ('cancelled', 'Отменена'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insurance_requests', verbose_name="Клиент")
    insurance_type = models.ForeignKey(InsuranceType, on_delete=models.PROTECT, verbose_name="Желаемый вид страхования")
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests', verbose_name="Назначенный агент")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус заявки")
    client_notes = models.TextField(blank=True, verbose_name="Примечание от клиента", help_text="Любые детали или вопросы, которые вы хотите уточнить.")
    agent_notes = models.TextField(blank=True, verbose_name="Примечания агента", help_text="Внутренние пометки для агента.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заявки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")

    def __str__(self):
        return f"Заявка №{self.id} от {self.client.username} на '{self.insurance_type.name}'"

    class Meta:
        verbose_name = "Заявка на страхование"
        verbose_name_plural = "Заявки на страхование"
        ordering = ['-created_at'] 