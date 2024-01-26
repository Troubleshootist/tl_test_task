import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from weather.services.yandex_weather import get_yandex_weather

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['weather'])
async def weather(message: types.Message):
    city = message.get_args()
    print(city)
    if not city:
        await message.reply("Введите название города после команды '/weather'")
        return

    weather_data = get_yandex_weather(city)
    if weather_data:
        await message.reply(f"Прогноз погоды для города {city}:\n"
                            f"Температура: {weather_data.temperature}\n"
                            f"Давление: {weather_data.pressure}\n"
                            f"Скорость ветра: {weather_data.wind_speed}")
    else:
        await message.reply("Извините, не удалось получить данные о погоде.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
