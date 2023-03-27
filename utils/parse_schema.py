from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urlunparse
from tqdm import tqdm
from .text_services import (
    preprocess_text,
    create_tfidf,
    get_top_tf_idf_words)
from .database_services import add_toast
from typing import List, Dict, Any
import logging


class PageParser:
    """
    Класс для парсинга сайтов с тостами
    """

    def __init__(self):
        self.url: str = ''
        self.site_name: str = ''
        self.session: Any = requests.session()
        self.ua: Any = UserAgent(verify_ssl=False)
        self.toasts: List[str] = None
        self.toasts_preprocessed: List[str] = []
        self.tags: List[str] = []
        self.tags_preprocessed: List[str] = []
        self.all_tags: Dict[str, int] = {}

    def get_soup(self, url: str) -> Any:
        """
        Получение "супа" сайта по url
        """
        try:
            req = self.session.get(url, headers={'User-Agent': self.ua.random})
        except Exception:
            # Если зашли сюда, значиит, какие-то проблемы с выбранным браузером и нужно попробовать снова
            return self.get_soup(url)
        page = req.text
        return BeautifulSoup(page, 'html.parser')

    def preprocess(self) -> None:
        """
        Обработка (токенизация + лемматизация) данных
        """
        logging.info(f"Preprocessing texts & tags for {self.site_name}...")
        for (i, toast) in tqdm(enumerate(self.toasts)):
            self.toasts_preprocessed.append(" ".join(preprocess_text(toast)))
            self.tags_preprocessed.append(preprocess_text(self.tags[i]))

    def write_to_db(self) -> None:
        """
        Создание tf-idf и добавление данных с сайтов в бд
        """
        logging.info(f"Building TfIdf for {self.site_name}...")
        toasts_tfidf, feature_names = create_tfidf(self.toasts_preprocessed)

        logging.info(f"Writing data from {self.site_name} to database...")
        for (i, text) in tqdm(enumerate(self.toasts)):
            # Вектор tf-idf для тоста
            toast_vector = toasts_tfidf[i, :]

            # Получаем список тегов-популярных лемм
            tags = get_top_tf_idf_words(toast_vector, feature_names, 10)

            # Объединяем список тегов-популярных лемм и тегов-разделов сайта
            tags = set(tags).union(set(self.tags_preprocessed[i]))

            # Добавляем тост и теги в БД, меняем словарь тегов
            self.all_tags = add_toast(tags, text, self.all_tags)[1]

    def parse_page_pozdravuha(self, url: str, header_tag: str) -> None:
        """
        Рекурсивный парсинг страниц раздела сайта pozdravuha.ru
        """
        # Получаем "суп" страницы
        page_soup = self.get_soup(url)

        # Находим все тосты на странице
        for toast in page_soup.find_all('p', {'class': 'item pozdravuha_ru_text'}):

            # Убираем ненужные теги
            for x in toast.findAll(['span', 'a', 'img', 'b', 'i']):
                x.extract()

            # Убираем ненужные символы из текста тоста
            toast = re.sub(r'\n+', '\n', re.sub(r'\r', '',
                           toast.get_text('\n').replace('\xa0', ' ')))

            # Добавляем тост и тег раздела в соответствующие списки
            if toast:
                self.toasts.append(toast)
                self.tags.append(header_tag)

        # Находим ссылку на следующую страницу
        next_page = page_soup.find('div', {'class': 'pages_next'})

        if next_page:
            # Заменяем путь в ссылке на следующую страницу и парсим ее
            next_page = urlunparse(urlparse(url)._replace(
                path=next_page.find('a')['href']))
            self.parse_page_pozdravuha(next_page, header_tag)

    def parse_pozdravuha(self) -> None:
        """
        Парсинг сайта pozdravuha.ru
        """
        # "Суп" главной страницы
        soup = self.get_soup(self.url)

        # Находим ссылки на все разделы с тостами
        for i in tqdm(soup.find('div', {'class': 'filters menu-block bg3 menu-left-subrazd'}).find_all('a')):
            # Заменяем путь в ссылке на раздел и парсим ее
            page_url = urlunparse(urlparse(self.url)._replace(path=i['href']))
            self.parse_page_pozdravuha(page_url, i.text)

    def parse_page_toast(self, url: str, header_tag: str) -> None:
        """
        Парсинг страницы сайта toast.ru
        """
        curr_toast = ''

        # "Суп" страницы
        soup = self.get_soup(url)

        # Находим все текстовые блоки
        for toast in soup.find_all('p')[1:]:

            # Если выполнились условия, то мы на промежуточном блоке м-ду тостами. Записываем текущий тост в список
            if len(toast.attrs) != 0 and curr_toast:
                # Убираем из тоста ненужные переносы и добавляем в списки тост и теги
                self.toasts.append(
                    re.sub(r'\n(?=[а-я])', r' ', curr_toast.strip()))
                self.tags.append(header_tag)
                curr_toast = ''

            # По этим параметрам отделяем тег с тостом от других тегов и добавляем его к текущему
            elif not toast.find('p') and not toast.find('font') and 'align' not in toast.attrs:
                curr_toast += toast.text + '\n'

        return soup

    def parse_toast(self) -> None:
        """
        Парсинг сайта toast.ru
        """

        # "Суп" главной страницы
        soup = self.get_soup(self.url)

        # Находим ссылки на все разделы с тостами
        for i in tqdm(soup.find_all('a', {'class': 'menutoast'})):
            # Заменяем путь в ссылке на раздел и парсим его
            page_url = urlunparse(urlparse(self.url)._replace(path=i['href']))

            # Тут нет кнопки "следующая страница", поэтому сперва парсим первую в разделе и находим ссылки на остальные страницы
            page_soup = self.parse_page_toast(page_url, i.text)
            t = page_soup.find('td', {'class': 'navlink'})

            # Если у нас больше одной страницы, то парсим остальные
            if t and len(t) > 1:
                for j in t.find_all('a')[1:]:
                    # Заменяем путь в ссылке на страницу раздела и парсим ее
                    new_url = urlunparse(
                        urlparse(self.url)._replace(path=j['href']))
                    self.parse_page_toast(new_url, i.text)

    def parse_alcofan(self) -> None:
        """
        Парсинг сайта alcofan.com
        """

        # "Суп" главной страницы
        soup = self.get_soup(self.url)

        # Находим ссылки на все разделы с тостами
        for i in tqdm(soup.find_all('a', {'rel': 'noopener'})):
            # Полная ссылка на раздел и тег раздела
            page_url = 'https:' + i['href']
            header_tag = i.text.strip()

            # "Суп" страницы раздела
            page_soup = self.get_soup(page_url)

            # Назодим все тосты (тут в разделах везде по 1 странице)
            page_info = page_soup.find('article').find_all('p')

            # Временные списки (нужны, тк в каждом разделе первый тег - описание раздела)
            page_toasts, page_tags = [], []

            for toast in page_info:
                # Отделяем от дрцгих тегов
                if toast.text not in ['', '*****'] and not toast.find('strong') and not toast.text.startswith('Тосты на'):
                    # Убираем ненужные символы из текста тоста и добавляем его и тег раздела в списки
                    page_toasts.append(toast.get_text(
                        '\n').replace('\xa0', ' ').lstrip(' *'))
                    page_tags.append(header_tag)

            # Теперь добавляем в общие списки
            self.toasts.extend(page_toasts[1:])
            self.tags.extend(page_tags[1:])

    def parse_site(self, url: str) -> None:
        """
        Объединяющая функция, в которую передается url
        """
        # Инициализиируем экземпляры всего, что только можно
        self.session = requests.session()
        self.ua = UserAgent(verify_ssl=False)
        self.url = url
        self.toasts, self.toasts_preprocessed, self.tags, self.tags_preprocessed = [], [], [], []

        # Это просто 1 слово - название сайта, чтобы не корячиться с длинными ссылками
        self.site_name = urlparse(url).netloc.split('.')[-2]

        # По этому слову определяем, какая ф-я нужна для парсинга
        logging.info(f"Parsing {self.site_name}...")
        if self.site_name == 'alcofan':
            self.parse_alcofan()
        elif self.site_name == 'toast':
            self.parse_toast()
        else:
            self.parse_pozdravuha()

        # Препроцессинг
        self.preprocess()

        # Tf-idf и БД
        self.write_to_db()
