import telebot
from core import TELEGRAM_API
from .bot_services import (
    start_response,
    main_menu,
    category_menu,
    gimme_tags,
    random_select,
    random_generate,
    toast_decider,
    text_decider)

# Создание экземпляра бота
bot = telebot.TeleBot(TELEGRAM_API)


@bot.message_handler(commands=["start"])
def start(message):
    """
    Endpoint для команды start
    """
    response, markup = start_response(chat_id=message.chat.id)
    bot.send_message(message.chat.id, response.format(
        message.chat.first_name), reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(commands=["help", "menu"])
def menu(message):
    """ 
    Endpoint для команд help и menu
    """
    response, markup = main_menu(
        chat_id=message.chat.id, help=message.text == "/help")
    bot.send_message(message.chat.id, response, reply_markup=markup,
                     parse_mode='Markdown')


@bot.message_handler(commands=["select_random_toast"])
def select_random(message):
    """
    Endpoint для команды select_random_toast (Выбери любой тост)
    """
    response, markup = random_select(chat_id=message.chat.id)
    bot.send_message(message.chat.id, response, reply_markup=markup,
                     parse_mode='Markdown')


@bot.message_handler(commands=["generate_random_toast"])
def generate_random(message):
    """
    Endpoint для команды generate_random_toast (Сгенерируй произвольный тост)
    """
    response, markup = random_generate(chat_id=message.chat.id)
    bot.send_message(message.chat.id, response, reply_markup=markup,
                     parse_mode='Markdown')


@bot.message_handler(commands=["select_keywords_toast", "generate_keywords_toast"])
def return_keywords_toast(message):
    """
    Endpoint для команд select_keywords_toast (Выбери тост по тегам) и generate_keywords_toast (Сгенерируй тост по тегам)
    """
    stage_name = 'select tag choose' if message.text == "/select_keywords_toast" else 'generate tag choose'
    response, markup = gimme_tags(
        chat_id=message.chat.id, stage_name=stage_name)
    bot.send_message(message.chat.id, response, reply_markup=markup,
                     parse_mode='Markdown')


@bot.message_handler(content_types=["text"])
def handle_text(message):
    """
    Endpoint для обработки текстовых запросов
    """
    if message.text in ["Перейти к использованию", "Расскажи, что ты умеешь!", "Мне нужна помощь", "На главную"]:
        response, markup = main_menu(
            chat_id=message.chat.id, help=message.text in ["Расскажи, что ты умеешь!", "Мне нужна помощь"])
    elif message.text in ["Сгенерируй тост", "Выбери тост"]:
        request = 'select menu' if message.text == "Выбери тост" else 'generate menu'
        response, markup = category_menu(
            stage_name=request, chat_id=message.chat.id)
    elif message.text in ["Тост по тегам", "Изменить теги"]:
        response, markup = gimme_tags(
            chat_id=message.chat.id, update=message.text == "Изменить теги")
    elif message.text in ["Рандомный тост", "👎", "👍"]:
        response, markup = toast_decider(
            chat_id=message.chat.id, prev_reaction=message.text != "👎")
    else:
        response, markup = text_decider(
            chat_id=message.chat.id, message=message.text)
    bot.send_message(message.chat.id, response,
                     reply_markup=markup, parse_mode='Markdown')
