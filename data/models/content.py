from sqlalchemy import Column, Integer, Text
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Content(SqlAlchemyBase, SerializerMixin):
    """Класс модели контента."""
    __tablename__ = 'contents'  # название таблицы с моделью в базе данных
    serialize_rules = ('-id',)  # правила преобразования объекта модели в json

    id = Column(Integer, autoincrement=True, primary_key=True)  # id контента
    content = Column(Text)  # контент
