from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Content(SqlAlchemyBase):
    __tablename__ = 'contents'

    id = Column(Integer, autoincrement=True, primary_key=True)
    content = Column(String)
