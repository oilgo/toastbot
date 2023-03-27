from sqlalchemy import (
    create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core import DATABASE

# Создаем sqlite engine
engine = create_engine(DATABASE)

# Создаем экземпляр БД (класс DeclarativeMeta)
Base = declarative_base()

# Создаем экземпляр класса для сессий
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
