import json
from .database import SessionLocal
from .models import (
    Toast,
    Stages,
    StageToUser,
    ToastToUser,
    Tag,
    ToastToTag,
    UserTags
)
from sqlalchemy import (
    update,
    and_,
    or_
)
from sqlalchemy.sql import func
from .text_services import (
    preprocess_text,
    create_tfidf,
    get_top_tf_idf_words
)
from typing import (
    Any,
    List,
    Dict,
    Tuple,
    Set,
    Union,
    Optional
)


def create_session() -> Any:
    """
    Создание сессии БД
    """
    session = SessionLocal()
    return session


def db_notempty() -> int:
    """
    Проверка, пустая ли наша БД
    """
    session = create_session()
    response = len(session.query(Toast).all())
    session.close()
    return response


def add_toast(tags: List[str], toast_text: str, all_tags: Dict[str, int]) -> Tuple[int, Dict[str, int]]:
    """
    Добавление тоста и его тегов в БД
    """
    session = create_session()

    # Добавляем тост в БД
    toast = Toast(
        toast_text=toast_text
    )
    session.add(toast)
    session.commit()

    for tag in tags:
        # Если такой тег уже был, достаем его значение из словаря
        if tag in all_tags:
            tag_id = all_tags[tag]

        # Если тег новый, добавляем в БД и в словарь
        else:
            new_tag = Tag(tag_name=tag)
            session.add(new_tag)
            session.commit()
            tag_id = new_tag.id
            all_tags[tag] = tag_id

        # Добавляем связь тост-тег в таблицу
        toast2tag = ToastToTag(
            toast_id=toast.id,
            tag_id=tag_id
        )
        session.add(toast2tag)
        session.commit()

    session.close()
    return toast.id, all_tags


def add_stage_name(stage: str) -> None:
    """
    Добавление названия "стадии" бота в БД
    """
    session = create_session()
    stage_class = Stages(stage_name=stage)
    session.add(stage_class)
    session.commit()
    session.close()


def get_last_stage(chat_id: int, return_id: Optional[bool] = False) -> str:
    """
    Последняя стадия, на которой был пользователь с chat_id
    return_id - если True, возвращаем id стадии; если Fasle, - название
    """
    session = create_session()
    stage_name = session.query(Stages.id if return_id else Stages.stage_name) \
        .join(StageToUser) \
        .filter(StageToUser.chat_id == chat_id) \
        .order_by(StageToUser.id.desc()) \
        .first()[0]
    session.close()
    return stage_name


def add_stage(chat_id: int, stage: Optional[str] = None, stage_id: Optional[int] = None) -> None:
    """
    Добавление записи о пользователе на стадии по названию стадии или по id стадии
    stage - название стадии
    stage_id - id стадии
    """
    session = create_session()
    if not stage_id:
        stage_id = int(session.query(Stages.id).filter(
            Stages.stage_name == stage).one()[0])
    stage2user = StageToUser(stage_id=stage_id, chat_id=chat_id)
    session.add(stage2user)
    session.commit()
    session.close()


def reaction_to_prev_select(chat_id: int) -> None:
    """
    Изменение реакции на последний выбранный тост на негативную
    """
    session = create_session()
    session.execute(
        update(ToastToUser)
        .where(ToastToUser.id == session.query(func.max(ToastToUser.id))
               .filter(ToastToUser.chat_id == chat_id)
               .group_by(ToastToUser.chat_id).subquery()
               ).values(user_like=False)
    )
    session.commit()
    session.close()


def reaction_to_prev_generate(chat_id: int) -> None:
    """
    Изменение реакции на последний сгенерированный тост на положительную
    """
    session = create_session()

    # Меняем реакцию пользователя в БД и получаем текст тоста
    gen_toast = session.execute(
        update(ToastToUser)
        .where(
            ToastToUser.id == session.query(func.max(ToastToUser.id))
            .filter(ToastToUser.chat_id == chat_id)
            .group_by(ToastToUser.chat_id).subquery()
        ).values(user_like=True)
        .returning(ToastToUser.generated_toast)
    ).fetchone()[0]

    # Составляем словарь всех существующих тегов
    all_tags = {tag[1]: int(tag[0])
                for tag in session.query(Tag.id, Tag.tag_name).all()}

    session.close()

    # Препроцессинг и tf-idf тоста, чтобы получить все теги
    toast_preprocessed = [" ".join(preprocess_text(gen_toast))]
    toasts_tfidf, feature_names = create_tfidf(toast_preprocessed)
    toast_vector = toasts_tfidf[0, :]
    tags = set(get_top_tf_idf_words(toast_vector, feature_names, 10))

    # Добавляем тост и теги в БД
    toast_id = add_toast(tags, gen_toast, all_tags)[0]

    # Меняем в таблице тост-пользователь текст тоста на id
    session = create_session()
    session.execute(
        update(ToastToUser)
        .where(ToastToUser.id == session.query(func.max(ToastToUser.id))
               .filter(ToastToUser.chat_id == chat_id)
               .group_by(ToastToUser.chat_id)
               .subquery()
               ).values(toast_id=toast_id, generated_toast=None)
    )
    session.commit()
    session.close()


def filter_unseen(session: Any, chat_id: int) -> Any:
    """
    Условие возвращает тосты, который пользователь не видел
    """
    return Toast.id \
        .not_in(
            session.query(ToastToUser.toast_id)
                .filter(and_(ToastToUser.chat_id == chat_id, ToastToUser.toast_id != None))
            .subquery()
        )


def filter_not_dislike(chat_id: int) -> Any:
    """
    Условие возвращает тосты, которым пользователь не поставил дизлайк
    """
    return and_(ToastToUser.chat_id == chat_id,
                or_(ToastToUser.user_like == None, ToastToUser.user_like == True))


def select_random_toasts(chat_id: int, all_toasts: Optional[bool] = False) -> Union[Tuple[str, int], List[str]]:
    """
    Выбор тостов без тегов - либо 1 рандомный, либо все без дизлайка от юзера (для генерации)
    all_toasts - True, если нужны все тосты; False, если нужен один
    """
    session = create_session()
    toasts = session.query(Toast.toast_text, Toast.id).join(
        ToastToUser, ToastToUser.toast_id == Toast.id, isouter=True)

    # Если нам не нужны все тосты, возвращаем 1 рандомный из тех, что юзер не видел
    if not all_toasts:
        response = toasts.filter(filter_unseen(
            session, chat_id)).order_by(func.random()).first()

    # Возвращаем все, которые юзер не дизлайкал
    else:
        response = [text[0]
                    for text in toasts.filter(filter_not_dislike(chat_id)).all()]

    session.close()
    return response


def select_tag_toasts(chat_id: int, all_toasts: Optional[bool] = False, message: Optional[str] = None) -> Union[None, List[str], Tuple[str, int]]:
    """
    Выбор тостов с тегами - либо 1 наиболее подходящий, либо все подходящие без дизлайка от юзера (для генерации)
    all_toasts - True, если нужны все тосты; False, если нужен один
    message - сообщение с тегами от пользователя. Если None, находим последние теги от пользователя
    """
    session = create_session()

    # Находим последние теги от пользователя
    if not message:
        tags = json.loads(
            session.query(UserTags.user_tags)
            .filter(UserTags.chat_id == chat_id)
            .order_by(UserTags.id.desc())
            .first()[0]
        )

    # Препроцессим теги и добавляем из в таблицу пользователь-теги в виде stringified list
    else:
        tags = preprocess_text(message)
        user_tags = UserTags(
            chat_id=chat_id,
            user_tags=json.dumps(tags, ensure_ascii=False)
        )
        session.add(user_tags)
        session.commit()

    # Находим наиболее подходящие тосты (по убыванию совпадающих тегов)
    toasts = session.query(Toast.toast_text, Toast.id) \
        .join(ToastToTag, ToastToTag.toast_id == Toast.id) \
        .join(Tag, Tag.id == ToastToTag.tag_id) \
        .filter(and_(Tag.tag_name.in_(tags),
                     filter_not_dislike(chat_id) if all_toasts else filter_unseen(session, chat_id))
                ).group_by(Toast.id) \
        .order_by(func.count(Tag.tag_name).desc()).all()

    # Если пусто, возвращаем None
    if not len(toasts):
        response = None

    # Если нужен 1 тост, возвращаем самый совпадающий по тегам
    elif not all_toasts:
        response = toasts[0]

    # Иначе возвращаем список всех тостов
    else:
        response = [text[0] for text in toasts]

    session.close()
    return response


def add_toast_seen(chat_id: int, gen_toast: Optional[str] = None, toast_id: Optional[int] = None) -> None:
    """
    Добавление тоста в "просмотренные" для пользователя 
    gen_toast - тут не пусто, если бот прислал сгенерированный тост
    toast_id - тут не пусто, если бот прислал тост из базы
    """
    session = create_session()
    toast_record = ToastToUser(
        chat_id=chat_id,
        generated_toast=gen_toast,
        toast_id=toast_id,
        user_like=toast_id != None, # По умолчанию считаем, что пользователям сгенерированные тосты не нравятся
    )
    session.add(toast_record)
    session.commit()
    session.close()


def get_all_generated(chat_id: int) -> Set[str]:
    """
    Получение множества всех сгенерированных тостов, которые видел юзер (чтобы не повторяться)
    """
    session = create_session()
    all_generated = session.query(ToastToUser.generated_toast).filter(
        ToastToUser.chat_id == chat_id).all()
    session.close()
    return {gen_toast[0] for gen_toast in all_generated}
