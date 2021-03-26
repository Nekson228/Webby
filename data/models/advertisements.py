from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from data.db_session import SqlAlchemyBase


class Advertisement(SqlAlchemyBase):
    __tablename__ = 'advertisements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    price = Column(Integer)
    content_id = Column(Integer, ForeignKey('contents.id'))

    author = relationship('User', back_populates='advertisements')
    content = relationship('Content')
    interests = relationship('Interest', secondary='advertisements_to_interests', backref='advertisements')
