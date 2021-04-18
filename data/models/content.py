from sqlalchemy import Column, Integer, Text
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Content(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'contents'
    serialize_rules = ('-id',)

    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(Text)
