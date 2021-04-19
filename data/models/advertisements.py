from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Advertisement(SqlAlchemyBase, SerializerMixin):
    """Класс модели объявления."""
    __tablename__ = 'advertisements'  # название таблицы с моделью в базе данных
    serialize_rules = ('-author.email', '-author.registration_time', '-author.interests', '-author_id',
                       '-content_id')  # правила преобразования объекта модели в json

    id = Column(Integer, primary_key=True, autoincrement=True)  # id объявления
    title = Column(String)  # название объявления
    author_id = Column(Integer, ForeignKey('users.id'))  # id автора объявления
    created_at = Column(DateTime, default=datetime.now)  # время создания объявления
    price = Column(Integer)  # стоимость объявления
    content_id = Column(Integer, ForeignKey('contents.id'))  # id содержания объявления

    author = relationship('User', back_populates='advertisements')  # объект автора объявления
    content = relationship('Content')  # объект содержания объявления
    interests = relationship('Interest', secondary='advertisements_to_interests',
                             backref='advertisements')  # объект интересов объявления

    def __repr__(self):
        return f'<Advertisement> {self.id}: {self.title}'
