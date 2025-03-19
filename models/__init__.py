from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

SqlAlchemyBase = declarative_base()
__factory = None

def global_init(db_url):
    global __factory

    # Используем PostgreSQL
    engine = create_engine(db_url, echo=False)
    __factory = sessionmaker(bind=engine)
    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    global __factory
    return __factory()
