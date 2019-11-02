from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, create_session
from sqlalchemy.ext.declarative import declarative_base

engine = None
Base = declarative_base()
db_session = scoped_session(lambda: create_session(bind=engine))


def init_engine(uri, **kwargs):
    global engine
    engine = create_engine(uri, **kwargs)
    return engine


def init_db():
    Base.metadata.create_all(bind=engine)
