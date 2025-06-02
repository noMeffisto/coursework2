from django.utils import timezone
from datetime import datetime
import calendar
import pytz
from .models import SiteSettings

def timezone_info(request):
    user_timezone = request.session.get('user_timezone', 'UTC')
    if user_timezone not in pytz.all_timezones:
        user_timezone = 'UTC'
    
    user_tz = pytz.timezone(user_timezone)
    utc_now = timezone.now()
    user_now = utc_now.astimezone(user_tz)
    
    cal = calendar.TextCalendar(calendar.MONDAY)
    current_calendar = cal.formatmonth(user_now.year, user_now.month)
    
    return {
        'user_timezone': user_timezone,
        'utc_now': utc_now.strftime('%d/%m/%Y %H:%M:%S'),
        'user_now': user_now.strftime('%d/%m/%Y %H:%M:%S'),
        'current_calendar': current_calendar,
    }

def site_settings(request):
    settings = SiteSettings.objects.first()
    current_year = datetime.now().year
    if not settings:
        default_copyright = f'© {current_year} CargoTransportation. Все права защищены.'
        settings = SiteSettings.objects.create(
            footer_copyright=default_copyright # Пример использования значения по умолчанию при создании
        )
    
    # Обрабатываем плейсхолдер {year} в тексте копирайта
    if settings.footer_copyright and '{year}' in settings.footer_copyright:
        processed_copyright = settings.footer_copyright.replace('{year}', str(current_year))
    elif not settings.footer_copyright: # Если копирайт пустой, ставим дефолтный
        processed_copyright = f'© {current_year} {settings.site_name or "CargoTransportation"}. Все права защищены.'
    else:
        processed_copyright = settings.footer_copyright

    return {
        'site_settings': settings, 
        'processed_footer_copyright': processed_copyright
    } 