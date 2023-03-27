# toastbot

Проект по программированию **Зиновьевой Ольги Михайловны** из группы **БКЛ-213**

[Бот в телеграме](https://t.me/ToastMakerBot), который выдает и генерирует тосты по тегам

Python Anywhere послал меня нафиг с моими библиотеками, поэтому запускать можно только локально...

### Как он работает
- Парсит сайты с тостами. Сейчас это https://alcofan.com, http://www.toast.ru и https://www.pozdravuha.ru
- Создает из этих тостов базу, где у каждого тоста несколько тегов. \
Теги - это:
    - Названия разделов на соответсвующих сайтах
    - Feature names, полученные с помощью tf-idf
- Дальше либо выбирает тост из имеющейся базы, либо генерирует его с помощью цепей Маркова и отправляет его пользователю

*Хостимся на http://oilgo.pythonanywhere.com/*

### Что делать, если вы хотите запустить бота у себя?
1. Клонируете этот репозиторий
2. Находите файлик **ENV.settings** и копируете его содержимое в созданный локально файлик .env
3. В консоли пишете:
```bash 
python -m venv venv
```
4. Дальше устанавливаете все библиотеки:
```bash
pip install -r requirements.txt
```
5. Запускаете:
```bash
python main.py
```
6. И наслаждаетесь!



