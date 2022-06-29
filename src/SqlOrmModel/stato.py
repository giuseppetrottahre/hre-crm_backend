from sqlalchemy import Column, String, Integer

from .base import Base,engine


class Stato(Base):
    __tablename__ = 'stati'
    id = Column(Integer, primary_key=True)
    #STEP 1
    stato=Column(String)

    def __init__(self, obj):
           for property, value in vars(obj).items():
               setattr(self,property,value)
        
