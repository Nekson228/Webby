from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Unicode, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    """Класс модели пользователя."""
    __tablename__ = 'users'  # название таблицы с моделью в базе данных
    serialize_rules = (
        '-advertisements', '-rank_id', '-admin', '-hashed_password')  # правила преобразования объекта модели в json

    id = Column(Integer, autoincrement=True, primary_key=True)  # id пользователя
    name = Column(Unicode)  # имя пользователя
    surname = Column(Unicode)  # фамилия пользователя
    birthday = Column(DateTime)  # день рождения пользователя
    email = Column(String, unique=True)  # email адресс пользователя
    phone_number = Column(String, unique=True)  # номер телефона пользователя
    hashed_password = Column(String)  # хэшированный пароль пользователя
    registration_time = Column(DateTime, default=datetime.now)  # время регистрации пользователя
    rating = Column(Integer, default=0)  # рейтинг пользователя
    rank_id = Column(Integer, ForeignKey('ranks.id'))  # id ранга пользователя
    admin = Column(Boolean, default=0)  # права пользователя

    advertisements = relationship('Advertisement', back_populates='author')  # объекты объявлений пользователя
    interests = relationship('Interest', secondary='users_to_interests',
                             backref='users')  # объекты интересов пользователя
    rank = relationship('Rank')  # объект ранга пользователя

    def set_password(self, password):
        """Метод, устанавливающий пользователю пароль.
        :param password: пароль, который необходимо установить"""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        """Метод, проверяющий пароль.
        :param password: пароль, который необходимо сравнить с паролем пользователя"""
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'<User> {self.id}: {self.name} {self.surname}'
