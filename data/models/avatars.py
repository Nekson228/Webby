from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Avatar(SqlAlchemyBase):
    __tablename__ = 'avatars'

    id = Column(Integer, autoincrement=True, primary_key=True)
    refers_to = Column(Integer, ForeignKey("users.id"))
    link = Column(String)
