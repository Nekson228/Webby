from sqlalchemy import Column, Integer, String

from data.db_session import SqlAlchemyBase


class Rank(SqlAlchemyBase):
    __tablename__ = 'ranks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
