from sqlalchemy import Column, Integer, String
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Rank(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'ranks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
