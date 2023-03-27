import os
from dotenv import load_dotenv

# Инициализация переменных окружения
load_dotenv()

# Ключ доступа к telegram боту
TELEGRAM_API = os.getenv(key="TELEGRAM_API")

# Адрес базы данных
DATABASE = os.getenv(key="DATABASE")

# Сайты для парсинга
PARSE_URLS = ['https://alcofan.com/luchshie-tosty-interneta',
        'http://www.toast.ru/toast/',
        'https://www.pozdravuha.ru/p/tosty']

# Стадии в боте
USER_STAGES = ['start',
          'main menu',
          'generate menu',
          'generate random',
          'generate tag choose',
          'generate tag',
          'select menu',
          'select random',
          'select tag choose',
          'select tag']
