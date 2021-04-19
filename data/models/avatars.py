from sqlalchemy import Column, Integer, String, ForeignKey

from data.db_session import SqlAlchemyBase


class Avatar(SqlAlchemyBase):
    """Класс модели аватара"""
    __tablename__ = 'avatars'  # название таблицы с моделью в базе данных

    id = Column(Integer, autoincrement=True, primary_key=True)  # id аватара
    refers_to = Column(Integer, ForeignKey("users.id"))  # id влвдельца аватара
    link = Column(String)  # путь до файла аватара
