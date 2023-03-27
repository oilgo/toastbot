from telebot import types
from utils import (
    add_stage,
    reaction_to_prev_generate,
    reaction_to_prev_select,
    get_last_stage,
    add_toast_seen,
    select_tag_toasts,
    select_random_toasts,
    get_all_generated
)
import markovify
import re
from pathlib import Path
from typing import (
    Tuple,
    List,
    Any,
    Optional
)

# Директория с файлами длинных сообщений
message_dir = Path(__file__).parent / 'messages'


def start_response(chat_id: int) -> Tuple[str, Any]:
    """
    Метод обработки команды start
    """
    # Добавляем стадию для юзера
    add_stage(stage='start', chat_id=chat_id)

    # Делаем кнопки
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.InlineKeyboardButton("Расскажи, что ты умеешь!")
    item2 = types.InlineKeyboardButton("Перейти к использованию")
    markup.add(item1, item2)

    # Берем нужное сообщение
    with open(message_dir / 'start.txt', 'r', encoding='utf-8') as start_message:
        message = start_message.read()
    return message, markup


def main_menu(chat_id: int, help: Optional[bool] = True) -> Tuple[str, Any]:
    """
    Метод для главного меню и команды help

    help: если True, сообщение для help; иначе для главного меню
    """
    # Добавляем стадию для юзера
    add_stage(stage='main menu', chat_id=chat_id)

    # Делаем кнопки
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.InlineKeyboardButton("Выбери тост")
    item2 = types.InlineKeyboardButton("Сгенерируй тост")
    markup.add(item1, item2)

    message = "Выбрать тост или сгенерировать его?"

    # Если юзеру нужна помощь, выбираем сообщение для помощи
    if help:
        with open(message_dir / 'help.txt', 'r', encoding='utf-8') as help_message:
            message = help_message.read()
    return message, markup


def category_menu(stage_name: str, chat_id: int) -> Tuple[str, Any]:
    """
    Метод для меню "Сгенерировать тост" и "Выбрать тост"
    """
    # Добавляем стадию для юзера
    add_stage(stage=stage_name, chat_id=chat_id)

    # Делаем кнопки
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.InlineKeyboardButton("Рандомный тост")
    item2 = types.InlineKeyboardButton("Тост по тегам")
    item3 = types.InlineKeyboardButton("На главную")
    markup.add(item1, item2, item3)

    message = "Вам нужен произвольный тост или тост по тегам?"
    return message, markup


def gimme_tags(chat_id: int, stage_name: Optional[str] = None, update: Optional[bool] = False) -> Tuple[str, Any]:
    """
    Метод для запроса тегов

    stage_name - None, если пользователь перешел по команде
    update - True, если юзер перешел по кнопке "Изменить теги", иначе False
    """
    # Добавляем стадию для юзера
    if not stage_name:
        stage_id = get_last_stage(chat_id, True)
        stage_id += -1 if update else 2  # ПрОиЗОШел ХаРдКоД
        add_stage(stage_id=stage_id, chat_id=chat_id)
    else:
        add_stage(stage=stage_name, chat_id=chat_id)

    # Убираем кнопки
    markup = types.ReplyKeyboardRemove()

    message = "Пришлите мне теги или описание тоста, например, _тост-притча_ или _тост на день рождения брата_"
    return message, markup


def get_markov(texts: List[str]) -> Any:
    """
    Метод получения модели Маркова
    """
    return markovify.Text(texts, state_size=3, retain_original=False)


def get_sentence_fit(model: Any, chat_id: int) -> str:
    """
    Находим подходящий сгенерированный тост
    """
    gen_toast = model.make_sentence()
    all_generated = get_all_generated(chat_id=chat_id)

    # Ищем, пока не найдем что-то, что юзер еще не видел и что не None
    while not gen_toast or gen_toast in all_generated:
        gen_toast = model.make_sentence()

    # Если Марков вздумает писать стишки
    gen_toast = re.sub('\s(?=[A-ZА-Я])', '\n', gen_toast)

    return gen_toast


def get_toast_markup(tags: Optional[bool] = False) -> Any:
    """
    Метод, который делает кнопки для всех разделов с тостами

    tags - True, если мы в разделе с тегами
    """
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.InlineKeyboardButton("👍")
    item2 = types.InlineKeyboardButton("👎")
    item3 = types.InlineKeyboardButton("На главную")
    markup.add(item1, item2, item3)

    # Если мы в разделе с тегами, +1 кнопка
    if tags:
        markup.add(types.InlineKeyboardButton("Изменить теги"))

    return markup


def tag_not_found():
    """
    Метод на случай, если пользователь указал долбанутые теги
    """
    message = 'По заданным тегам не найдено ни одного тоста ☹️'

    # Делаем кнопки
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.InlineKeyboardButton("Изменить теги")
    item2 = types.InlineKeyboardButton("На главную")
    markup.add(item1, item2)

    return message, markup


def random_generate(chat_id: int) -> Tuple[str, Any]:
    """
    Метод для генерации рандомного тоста
    """
    # Добавляем стадию для юзера
    add_stage(stage='generate random', chat_id=chat_id)

    # Создаем модель по всем недизлаканным тостам
    model = get_markov(texts=select_random_toasts(chat_id, True))

    # Генерируем супер тост
    gen_toast = get_sentence_fit(model=model, chat_id=chat_id)

    # Фиксируем тост в БД
    add_toast_seen(chat_id=chat_id, gen_toast=gen_toast)

    return gen_toast, get_toast_markup()


def tags_generate(chat_id: int, message: Optional[str] = None) -> Tuple[str, Any]:
    """
    Метод для генерации тоста по тегам

    message - не None, если юзер только что указал теги
    """
    # Добавляем стадию для юзера
    add_stage(stage='generate random', chat_id=chat_id)

    # Пытаемся найти тосты по тегам
    tag_toasts = select_tag_toasts(
        chat_id=chat_id, all_toasts=True, message=message)
    if not tag_toasts:
        return tag_not_found()

    # Создаем модель
    tag_model = get_markov(texts=tag_toasts)

    # Генерируем супер тост
    gen_toast = get_sentence_fit(model=tag_model, chat_id=chat_id)

    # Фиксируем тост в БД
    add_toast_seen(chat_id=chat_id, gen_toast=gen_toast)

    return gen_toast, get_toast_markup(tags=True)


def random_select(chat_id: int) -> Tuple[str, Any]:
    """
    Метод для выбора рандомного тоста
    """
    # Добавляем стадию для юзера
    add_stage(stage='select random', chat_id=chat_id)

    # Добываем тост
    toast = select_random_toasts(chat_id=chat_id)

    # Фиксируем тост в БД
    add_toast_seen(chat_id=chat_id, toast_id=int(toast[1]))

    return toast[0], get_toast_markup()


def tags_select(chat_id: int, message: Optional[str] = None) -> Tuple[str, Any]:
    """
    Метод для выбора тоста по тегам

    message - не None, если юзер только что указал теги
    """
    # Добавляем стадию для юзера
    add_stage(stage='select tag', chat_id=chat_id)

    # Добываем тост
    toast = select_tag_toasts(chat_id=chat_id, message=message)
    if not toast:
        return tag_not_found()

    # Фиксируем тост в БД
    add_toast_seen(chat_id=chat_id, toast_id=int(toast[1]))
    return toast[0], get_toast_markup(True)


def toast_decider(chat_id: int, prev_reaction: Optional[bool] = True) -> Tuple[str, Any]:
    """
    Метод для обработки кнопок. 
    Решает, куда нам идти (вызывается, когда юзер жмет кнопку, которая у нас в нескольких разделах)

    prev_reaction - если нажал лайк или дизлайк
    """
    # Получаем предыдущее действие (стадию) юзера
    stage_name = get_last_stage(chat_id=chat_id)

    # Если мы присылали тост из БД, и юзеру он не понравился
    if stage_name in ['select random', 'select tag'] and not prev_reaction:
        reaction_to_prev_select(chat_id=chat_id)

    # Если мы присылали сгенерированный тост, и юзеру он понравился
    elif stage_name in ['generate random', 'generate_tag'] and prev_reaction:
        reaction_to_prev_generate(chat_id=chat_id)

    # Решаем, что делать
    if stage_name in ['select menu', 'select random']:
        return random_select(chat_id=chat_id)
    elif stage_name in ['generate menu', 'generate random']:
        return random_generate(chat_id=chat_id)
    elif stage_name == 'select tag':
        return tags_select(chat_id=chat_id)

    return tags_generate(chat_id=chat_id)


def text_decider(chat_id: int, message: str) -> Tuple[str, Any]:
    """
    Метод для обработки текста с клавиатуры 
    """
    # Получаем предыдущее действие (стадию) юзера
    stage_name = get_last_stage(chat_id=chat_id)
    if stage_name == 'select tag choose':
        message, markup = tags_select(chat_id=chat_id, message=message)
    elif stage_name == 'generate tag choose':
        message, markup = tags_generate(chat_id=chat_id, message=message)
    
    # Если юзер решил просто пообщаться с ботом, а он не хочет
    else:
        # Делаем кнопки
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        item1 = types.InlineKeyboardButton("Мне нужна помощь")
        item2 = types.InlineKeyboardButton("На главную")
        markup.add(item1, item2)

        # Берем сообщение для непонимулек
        with open(message_dir / 'not_understood.txt', 'r', encoding='utf-8') as not_understand_message:
            message = not_understand_message.read()
    
    return message, markup
