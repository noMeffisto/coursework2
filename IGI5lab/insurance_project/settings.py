import os # Убедитесь, что os импортирован в начале файла
from pathlib import Path # Добавим импорт Path

# Определяем BASE_DIR как родительскую директорию файла settings.py
# Это означает, что BASE_DIR будет указывать на папку 'insurance_project'
# Если manage.py находится уровнем выше, то BASE_DIR должен быть Path(__file__).resolve().parent.parent
# Судя по вашей структуре (manage.py в 'андр', settings.py в 'андр/insurance_project'),
# BASE_DIR должен указывать на 'C:/Users/rost2/OneDrive/Рабочий стол/андр'
BASE_DIR = Path(__file__).resolve().parent.parent

# Параметры безопасности
# ВНИМАНИЕ: не запускайте проект с DEBUG = True в производственной среде!
DEBUG = True # Устанавливаем DEBUG в True для разработки

ALLOWED_HOSTS = ['127.0.0.1', 'localhost'] # Стандартные хосты для локальной разработки

# Application definition
# Здесь должны быть INSTALLED_APPS, MIDDLEWARE и т.д.
# Убедимся, что эти секции присутствуют, если их нет.

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'insurance_app', # Наше приложение
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'insurance_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
] 

# Настройки редиректа для аутентификации
LOGIN_REDIRECT_URL = 'insurance_app:home'  # Куда перенаправлять после успешного входа
LOGOUT_REDIRECT_URL = 'insurance_app:home' # Куда перенаправлять после выхода (если не указано в LogoutView.next_page)
LOGIN_URL = 'insurance_app:login'          # URL страницы входа

# Настройки для отправки email (для сброса пароля)
# В режиме разработки письма будут выводиться в консоль
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Если нужно настроить реальный SMTP сервер:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your_email@example.com'
# EMAIL_HOST_PASSWORD = 'your_password'
# DEFAULT_FROM_EMAIL = 'webmaster@localhost' # Адрес отправителя по умолчанию

# Настройки статических файлов
STATIC_URL = 'static/' # URL-префикс для статических файлов

# Директории, где Django будет искать статические файлы в режиме разработки
STATICFILES_DIRS = [
    BASE_DIR / "static", # Общая папка static на уровне проекта
]

# MEDIA_URL и MEDIA_ROOT для загружаемых пользователем файлов (например, изображений)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Настройки базы данных (по умолчанию sqlite3)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Настройки интернационализации и локализации
LANGUAGE_CODE = 'ru-ru' # Установим русский язык
TIME_ZONE = 'Europe/Moscow' # Установим часовой пояс (пример)
USE_I18N = True
USE_L10N = True # Важно для форматирования дат, чисел
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# SECRET_KEY - должен быть уникальным и секретным в производственной среде
# Для разработки можно сгенерировать простой ключ.
# ВНИМАНИЕ: Замените это на сложный ключ перед развертыванием!
import secrets
SECRET_KEY = secrets.token_hex(32) # Генерируем простой ключ для разработки 

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
} 