from sqlalchemy import Column, Integer, Unicode, Table, ForeignKey
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase

ad_table = Table(
    'advertisements_to_interests',
    SqlAlchemyBase.metadata,
    Column('advertisements', Integer, ForeignKey('advertisements.id')),
    Column('interests', Integer, ForeignKey('interests.id'))
)  # промежуточная таблица для отношения объявлений к интересам

user_table = Table(
    'users_to_interests',
    SqlAlchemyBase.metadata,
    Column('users', Integer, ForeignKey('users.id')),
    Column('interests', Integer, ForeignKey('interests.id'))
)  # промежуточная таблица для отношения пользователей к интересам


class Interest(SqlAlchemyBase, SerializerMixin):
    """Класс модели интереса."""
    __tablename__ = 'interests'  # название таблицы с моделью в базе данных
    serialize_rules = ('-advertisements', '-users')  # правила преобразования объекта модели в json

    id = Column(Integer, primary_key=True, autoincrement=True)  # id интереса
    title = Column(Unicode, nullable=True)  # название интереса
