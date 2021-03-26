from sqlalchemy import Column, Integer, Unicode, Table, ForeignKey
from data.db_session import SqlAlchemyBase

ad_table = Table(
    'advertisements_to_interests',
    SqlAlchemyBase.metadata,
    Column('advertisements', Integer, ForeignKey('advertisements.id')),
    Column('interests', Integer, ForeignKey('interests.id'))
)

user_table = Table(
    'users_to_interests',
    SqlAlchemyBase.metadata,
    Column('users', Integer, ForeignKey('users.id')),
    Column('interests', Integer, ForeignKey('interests.id'))
)


class Interest(SqlAlchemyBase):
    __tablename__ = 'interests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Unicode, nullable=True)
