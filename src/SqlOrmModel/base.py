from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .. import config as cfg

engine = create_engine(cfg.database)

Session = sessionmaker(bind=engine)

Base = declarative_base()
