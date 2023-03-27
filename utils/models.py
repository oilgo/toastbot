from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    PrimaryKeyConstraint)
from sqlalchemy.sql import expression
from .database import Base


class ToastToUser(Base):
    """
    Таблица с информацией о том, какой тост мы кому послали
    """
    __tablename__ = 'toast_to_user'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    generated_toast = Column(String(4000))
    toast_id = Column('toast_id', Integer, ForeignKey(
        "toasts.id", ondelete="cascade"))
    user_like = Column(Boolean, server_default=expression.true())


class Stages(Base):
    """
    Таблица с названиями всех "стадий" бота
    """
    __tablename__ = 'stages'
    id = Column(Integer, primary_key=True)
    stage_name = Column(String(100))


class StageToUser(Base):
    """
    Таблица с информацией о том, на какой стадии какой пользователь
    """
    __tablename__ = 'stage_to_user'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    stage_id = Column('stage_id', Integer, ForeignKey(
        "stages.id", ondelete="cascade"))


class UserTags(Base):
    """
    Таблица с информацией о том, какие теги какой пользователь вводил
    """
    __tablename__ = 'user_tags'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    user_tags = Column(String(4000))


class Toast(Base):
    """
    Таблица с текстами тостов
    """
    __tablename__ = 'toasts'
    id = Column(Integer, primary_key=True)
    toast_text = Column(String(4000))


class Tag(Base):
    """
    Таблица с текстами тегов
    """
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    tag_name = Column(String(100))


class ToastToTag(Base):
    """
    Таблица связей тостов и тегов
    """
    __tablename__ = 'toast_to_tag'
    __table_args__ = (PrimaryKeyConstraint('toast_id', 'tag_id'),)

    toast_id = Column('toast_id', ForeignKey(
        'toasts.id', ondelete="cascade"), primary_key=True)
    tag_id = Column('tag_id', ForeignKey(
        'tags.id', ondelete="cascade"), primary_key=True)
