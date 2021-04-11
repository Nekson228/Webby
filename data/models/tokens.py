from data.db_session import SqlAlchemyBase

from sqlalchemy import Column, String, Integer


class Token(SqlAlchemyBase):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String)
