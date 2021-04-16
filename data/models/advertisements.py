from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Advertisement(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'advertisements'
    serialize_rules = ('-author.email', '-author.rating', '-author.hashed_password', '-author.registration_time',
                       '-author.admin', '-author.interests')

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)
    price = Column(Integer)
    content_id = Column(Integer, ForeignKey('contents.id'))

    author = relationship('User', back_populates='advertisements')
    content = relationship('Content')
    interests = relationship('Interest', secondary='advertisements_to_interests', backref='advertisements')

    def __repr__(self):
        return f'<Advertisement> {self.id}: {self.title}'
