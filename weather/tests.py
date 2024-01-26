import os
import unittest
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock

import django
from django.test import Client
import requests

from weather.exceptions import (
    NoCityFound,
    FileWithCoordsNotFound,
    CoordsParsingException,
    YandexWeatherDataFetchError,
)
from weather.services.yandex_weather import Weather

# Устанавливаем переменную окружения, указывающую Django на ваш файл настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_project_tl.settings')

# Обязательно вызываем django.setup() перед импортом модулей Django или обращением к его настройкам
django.setup()


class TestGetLatAndLon(unittest.TestCase):
    @patch("weather.services.yandex_weather.load_workbook")
    def test_existing_city(self, mock_load_workbook):
        mock_sheet = mock_load_workbook.return_value.active
        mock_sheet.iter_rows.return_value = [("Moscow", "", "", 55.755826, 37.6173)]

        from weather.services.yandex_weather import get_lat_and_lon

        lat, lon = get_lat_and_lon("Moscow")
        self.assertAlmostEqual(lat, 55.755826, places=4)
        self.assertAlmostEqual(lon, 37.6173, places=4)

    @patch("weather.services.yandex_weather.load_workbook")
    def test_non_existing_city(self, mock_load_workbook):
        mock_sheet = mock_load_workbook.return_value.active
        mock_sheet.iter_rows.return_value = []

        from weather.services.yandex_weather import get_lat_and_lon

        with self.assertRaises(NoCityFound):
            get_lat_and_lon("NonExistingCity")

    @patch("weather.services.yandex_weather.load_workbook", side_effect=FileNotFoundError)
    def test_missing_file(self, mock_load_workbook):
        from weather.services.yandex_weather import get_lat_and_lon

        with self.assertRaises(FileWithCoordsNotFound):
            get_lat_and_lon("AnyCity")

    @patch("weather.services.yandex_weather.load_workbook", side_effect=Exception)
    def test_parsing_error(self, mock_load_workbook):
        from weather.services.yandex_weather import get_lat_and_lon

        with self.assertRaises(CoordsParsingException):
            get_lat_and_lon("AnyCity")


class TestGetYandexWeather(unittest.TestCase):
    @patch("weather.services.yandex_weather.get_lat_and_lon", return_value=(55.755826, 37.6173))
    @patch("weather.services.yandex_weather.requests.get")
    def test_successful_weather_request(self, mock_requests_get, mock_get_lat_and_lon):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "fact": {"temp": -5, "pressure_mm": 760, "wind_speed": 3, "obs_time": 1642742400}
        }
        mock_requests_get.return_value = mock_response

        from weather.services.yandex_weather import get_yandex_weather, Weather

        weather = get_yandex_weather("Moscow")

        self.assertIsInstance(weather, Weather)
        self.assertEqual(weather.temperature, -5)
        self.assertEqual(weather.pressure, 760)
        self.assertEqual(weather.wind_speed, 3)
        self.assertEqual(weather.observed_at, datetime.fromtimestamp(1642742400))

    @patch("weather.services.yandex_weather.get_lat_and_lon", return_value=(55.755826, 37.6173))
    @patch(
        "weather.services.yandex_weather.requests.get",
        side_effect=requests.exceptions.RequestException,
    )
    def test_weather_request_failure(self, mock_requests_get, mock_get_lat_and_lon):
        from weather.services.yandex_weather import get_yandex_weather

        with self.assertRaises(YandexWeatherDataFetchError):
            get_yandex_weather("Moscow")


class WeatherTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @patch('weather.views.yandex_weather_cache', {})
    @patch('weather.views.get_yandex_weather')
    def test_weather_cache(self, mock_get_yandex_weather):
        # Устанавливаем мок для get_yandex_weather
        mock_weather_data = Weather(
            temperature=2, pressure=752, wind_speed=3, observed_at=datetime.now()
        )
        mock_get_yandex_weather.return_value = mock_weather_data

        response = self.client.get('/weather/', {'city': 'Москва'})
        self.assertEqual(200, response.status_code)

        response = self.client.get('/weather/', {'city': 'Москва'})
        self.assertEqual(200, response.status_code)

        self.assertEqual(1, mock_get_yandex_weather.call_count)

    @patch('weather.views.get_yandex_weather')
    def test_get_weather_yandex_data_fetch_error(self, mock_get_yandex_weather):
        mock_get_yandex_weather.side_effect = YandexWeatherDataFetchError("Test Yandex Error")

        response = self.client.get('/weather/?city=TestCity')
        self.assertEqual(response.status_code, 400)

    @patch('weather.views.get_yandex_weather')
    def test_get_weather_file_with_coords_not_found(self, mock_get_yandex_weather):
        mock_get_yandex_weather.side_effect = FileWithCoordsNotFound("Test File Not Found Error")

        response = self.client.get('/weather/?city=TestCity')
        self.assertEqual(response.status_code, 400)

    @patch('weather.views.get_yandex_weather')
    def test_get_weather_coords_parsing_exception(self, mock_get_yandex_weather):
        mock_get_yandex_weather.side_effect = CoordsParsingException("Test Parsing Exception Error")

        response = self.client.get('/weather/?city=TestCity')
        self.assertEqual(response.status_code, 400)

    @patch('weather.views.get_yandex_weather')
    def test_get_weather_no_city_found(self, mock_get_yandex_weather):
        mock_get_yandex_weather.side_effect = NoCityFound("Test No City Found Error")

        response = self.client.get('/weather/?city=TestCity')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
