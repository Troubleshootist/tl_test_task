from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime

from weather.exceptions import (
    YandexWeatherDataFetchError,
    FileWithCoordsNotFound,
    CoordsParsingException,
    NoCityFound,
)
from weather.services.yandex_weather import get_yandex_weather
from weather_project_tl.settings import YANDEX_REQUEST_TIME_DELAY

yandex_weather_cache = {}


@require_GET
def get_weather(request):
    city_name = request.GET.get("city")

    if not city_name:
        return JsonResponse(
            {"error": "Параметр city отсутствует в запросе"}, status=400
        )

    if (
        city_name in yandex_weather_cache
        and (datetime.now() - yandex_weather_cache[city_name].observed_at).seconds
        < YANDEX_REQUEST_TIME_DELAY
    ):
        return JsonResponse(yandex_weather_cache[city_name].dict())

    try:
        weather_data = get_yandex_weather(city_name)
        yandex_weather_cache[city_name] = weather_data
        return JsonResponse(weather_data.dict())
    except YandexWeatherDataFetchError as e:
        return JsonResponse(
            {"error": f"Ошибка при получении данных от yandex: {str(e)}"}, status=400
        )
    except FileWithCoordsNotFound as e:
        return JsonResponse(
            {"error": f"Файл с данными о координатах не найден: {str(e)}"}, status=400
        )
    except CoordsParsingException as e:
        return JsonResponse(
            {"error": f"Ошибка при парсинге файла с координатами: {str(e)}"}, status=400
        )
    except NoCityFound as e:
        return JsonResponse(
            {"error": f"Город не найден в файле с координатами: {str(e)}"}, status=400
        )
