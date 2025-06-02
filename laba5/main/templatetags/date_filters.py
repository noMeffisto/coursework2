from django import template
from django.utils import timezone
import pytz

register = template.Library()

@register.filter(name='format_datetime')
def format_datetime(value, user_timezone='UTC'):
    if not value:
        return ''
    
    try:
        if not timezone.is_aware(value):
            value = timezone.make_aware(value, pytz.UTC)
        
        user_tz = pytz.timezone(user_timezone)
        local_dt = value.astimezone(user_tz)
        return local_dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return value 