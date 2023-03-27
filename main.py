from utils import (
    Base,
    engine,
    PageParser,
    add_stage_name,
    db_notempty

)
from telegram_bot import bot
from core import USER_STAGES, PARSE_URLS
import logging


def main():
    # Создание базы данных
    Base.metadata.create_all(engine)

    # Создание лога
    logging.basicConfig(filename="./logs/app_log.log", filemode="w",
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.captureWarnings(True)

    # Если в базе нет записей
    if not db_notempty():
        parser = PageParser()

        # Парсим все сайты
        for url in PARSE_URLS:
            parser.parse_site(url)

        # Пишем в базу все "стадии" пользователя в боте
        logging.info('Writing app stage names')
        for stage in USER_STAGES:
            add_stage_name(stage)

        logging.info('Data created!')

    bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    main()
