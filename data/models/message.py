from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Message(SqlAlchemyBase, SerializerMixin):
    """Класс модели сообщения."""
    __tablename__ = 'messages'  # название таблицы с моделью в базе данных
    serialize_rules = ('-sender', '-receiver', '-content_id')  # правила преобразования объекта модели в json

    id = Column(Integer, autoincrement=True, primary_key=True)  # id сообщения
    to_id = Column(Integer, ForeignKey("users.id"))  # id получателя сообщения
    from_id = Column(Integer, ForeignKey("users.id"))  # id отправителя сообщения
    content_id = Column(Integer, ForeignKey("contents.id"))  # id содержания сообщения
    created_at = Column(DateTime, default=datetime.now)  # время создания сообщения

    sender = relationship("User", foreign_keys=[from_id])  # объект отправителя сообщения
    receiver = relationship("User", foreign_keys=[to_id])  # объект получателя сообщения
    content = relationship("Content")  # объект содержания сообщения

    def __repr__(self):
        return f'<Message> {self.id}: from {self.sender} to {self.receiver}: "{self.content.content}"'
