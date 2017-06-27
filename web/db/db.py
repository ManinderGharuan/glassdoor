from os import path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
Scraper_Base = declarative_base()
User_Base = declarative_base()


def get_session():
    engine = create_engine('sqlite:///glassdoor.db')

    if not path.exists('glassdoor.db'):
        Base.metadata.create_all(engine)

    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    return session


def get_scraper_session():
    engine = create_engine('sqlite:///scraper.db')

    if not path.exists('scraper.db'):
        Scraper_Base.metadata.create_all(engine)

    Scraper_Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)

    return DBSession()


def get_user_session():
    engine = create_engine('sqlite:///user.db')

    if not path.exists('user.db'):
        User_Base.metadata.create_all(engine)

    User_Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)

    return DBSession()
