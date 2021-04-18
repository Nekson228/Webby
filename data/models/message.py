from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Message(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'messages'
    serialize_rules = ('-sender', '-receiver', '-content_id')

    id = Column(Integer, autoincrement=True, primary_key=True)
    to_id = Column(Integer, ForeignKey("users.id"))
    from_id = Column(Integer, ForeignKey("users.id"))
    content_id = Column(Integer, ForeignKey("contents.id"))
    created_at = Column(DateTime, default=datetime.now)
    sender = relationship("User", foreign_keys=[from_id])
    receiver = relationship("User", foreign_keys=[to_id])
    content = relationship("Content")

    def __repr__(self):
        return f'<Message> {self.id}: from {self.sender} to {self.receiver}: "{self.content.content}"'
