from sqlalchemy import Column, String,Integer,DateTime,Boolean,func
from .base import Base,engine


class BackendUser(Base):
    __tablename__ = 'backend_user'
    id = Column(Integer, primary_key=True)
    username=Column(String)
    password=Column(String)
    email=Column(String)
    permissions=Column(String)
    firstlogin=Column(Boolean)
    querysearch= Column(String,default="") #nome,cognome,email
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestamp= Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
    
 
    
  
    def __init__(self, obj):
           for property, value in vars(obj).items():
               setattr(self,property.lower(),value)