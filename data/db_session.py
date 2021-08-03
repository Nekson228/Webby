import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from sqlalchemy import MetaData
import sqlalchemy.ext.declarative as dec

meta = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
      })
SqlAlchemyBase = dec.declarative_base(metadata=meta)

__factory = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    # if not db_file or not db_file.strip():
        # raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'postgres://brpdhqzqtofrfy:12d3006a03c3e69e07b9c6cb44f966c1cc6ab0f0e62fcf0cfab3879be866dcf7@ec2-34-253-116-145.eu-west-1.compute.amazonaws.com:5432/d4qb438aat76vb'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
