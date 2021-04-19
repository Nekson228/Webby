from sqlalchemy import Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Rank(SqlAlchemyBase, SerializerMixin):
    """Класс модели ранга."""
    __tablename__ = 'ranks'  # название таблицы с моделью в базе данных

    id = Column(Integer, primary_key=True, autoincrement=True)  # id ранга
    title = Column(String)  # название ранга
