from django.contrib import admin
from django.urls import path, include # Убедитесь, что include импортирован
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('insurance_app.urls')), # Подключаем URL-адреса нашего приложения
    path('core/', include('core.urls')),  # Добавляем URL для core приложения
    # Другие пути вашего проекта, если они есть
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT if hasattr(settings, 'STATIC_ROOT') else None)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 