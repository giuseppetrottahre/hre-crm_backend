from sqlalchemy import Column, String,Integer,DateTime,func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base


class BackendUserSession(Base):
    __tablename__ = 'backend_user_session'
    session_id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    user_id=Column(String)
    callcount=Column(Integer,default=0)
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestmp=Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
 
    
  
    def __init__(self, user_id):
           self.user_id=user_id