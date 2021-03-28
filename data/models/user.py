from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Unicode, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode)
    surname = Column(Unicode)
    birthday = Column(DateTime)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    hashed_password = Column(String)
    registration_time = Column(DateTime, default=datetime.now)
    rating = Column(Integer, default=0)
    rank = Column(Unicode)
    position = Column(Integer)

    advertisements = relationship('Advertisement', back_populates='author')
    interests = relationship('Interest', secondary='users_to_interests', backref='users')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'<User> {self.id}: {self.name} {self.surname}'
