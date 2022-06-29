from sqlalchemy import Column, String, Integer

from .base import Base,engine


class Comune(Base):
    __tablename__ = 'comuni'
    id = Column(Integer, primary_key=True)
    #STEP 1
    comune=Column(String)
    regione=Column(String)
    provincia=Column(String)
    codicecatastale=Column(String)
    cap=Column(String)
    

    def __init__(self, obj):
           for property, value in vars(obj).items():
               setattr(self,property,value)
        