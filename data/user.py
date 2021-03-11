from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String)
    surname = Column(String)
    birthday = Column(DateTime)
    email = Column(String, unique=True)
    phone_number = Column(String, unique=True)
    hashed_password = Column(String)
    registration_time = Column(DateTime, default=datetime.now())
