from django.shortcuts import render
from django.utils import timezone
import datetime
import requests
import logging

logger = logging.getLogger(__name__)

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
    
    context = {
        'quote': quote,
        'weather': weather,
        'now': now,
        'now_utc': now_utc,
        'now_utc_minus3': now_utc_minus3,
        'TIME_ZONE': timezone.get_current_timezone_name(),
    }
    logger.info(f"Context data: {context}")
    return render(request, 'insurance_app/privacy_policy.html', context) 