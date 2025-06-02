from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.services.external_api import get_weather_for_city, get_coordinates

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_privacy_policy_view(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/privacy.html')

class ExternalAPITestCase(TestCase):
    @patch('requests.get')
    def test_get_weather_for_city(self, mock_get):
        # Подготовка мок-ответа
        mock_get.return_value.json.return_value = {
            'main': {'temp': 20, 'humidity': 65},
            'weather': [{'description': 'ясно'}],
            'wind': {'speed': 5}
        }
        mock_get.return_value.raise_for_status.return_value = None

        # Вызов функции
        result = get_weather_for_city('Минск')

        # Проверка результата
        self.assertEqual(result['temperature'], 20)
        self.assertEqual(result['description'], 'ясно')
        self.assertEqual(result['humidity'], 65)
        self.assertEqual(result['wind_speed'], 5)

    @patch('requests.get')
    def test_get_coordinates(self, mock_get):
        # Подготовка мок-ответа
        mock_get.return_value.json.return_value = [{
            'lat': '53.9',
            'lon': '27.5667',
            'display_name': 'Минск, Беларусь'
        }]
        mock_get.return_value.raise_for_status.return_value = None

        # Вызов функции
        result = get_coordinates('Минск')

        # Проверка результата
        self.assertEqual(result['lat'], 53.9)
        self.assertEqual(result['lon'], 27.5667)
        self.assertEqual(result['display_name'], 'Минск, Беларусь') 