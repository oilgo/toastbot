from string import punctuation
from nltk.tokenize import word_tokenize
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from typing import List, Any, Tuple

# Экземпляр класса MorphAnalyzer
morph = MorphAnalyzer()
# Стоп-слова
stop_words = set(stopwords.words('russian'))


def preprocess_text(message: str) -> List[str]:
    """
    Преобразование текста в список лемм
    """
    return [morph.parse(token.strip(punctuation + '–'))[0].normal_form.replace('h', 'н')
            for token in word_tokenize(message)
            if token.strip(punctuation + '–') and token not in stop_words and not token.isdigit()]


def get_top_tf_idf_words(tfidf_vector: Any, feature_names: Any, top_n: int) -> Any:
    """
    Получение n самых важных слов по tf-idf
    """
    sorted_nzs = np.argsort(tfidf_vector.data)[:-(top_n+1):-1]
    return feature_names[tfidf_vector.indices[sorted_nzs]]


def create_tfidf(text_array: List[str]) -> Tuple[Any, Any]:
    """
    Создание экземпляра tf-idf и получение feature names
    """
    tfidf = TfidfVectorizer(stop_words=list(stop_words), max_features=10000)
    texts_tfidf = tfidf.fit_transform(text_array)
    feature_names = np.array(tfidf.get_feature_names_out())
    return texts_tfidf, feature_names
