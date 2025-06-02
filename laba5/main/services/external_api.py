import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_weather_for_city(city):
    """
    Получение погодных данных через OpenWeatherMap API
    """
    try:
        api_key = settings.OPENWEATHERMAP_API_KEY
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            'temperature': round(data['main']['temp']),
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
    except Exception as e:
        logger.error(f"Error getting weather data: {str(e)}")
        return None

def get_coordinates(address):
    """
    Получение координат через Nominatim API (OpenStreetMap)
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
        headers = {
            'User-Agent': 'CargoTransApp/1.0'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
        return None
    except Exception as e:
        logger.error(f"Error getting coordinates: {str(e)}")
        return None 