from sqlalchemy import Column, String, Integer, Date,Boolean,DateTime,func
from sqlalchemy.dialects.postgresql import UUID

import uuid
from .base import Base,engine


class UserTimesheet(Base):
    __tablename__ = 'crm_user_timesheet'
    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    id_user=Column(String)
    nome=Column(String)
    secondonome=Column(String)
    cognome=Column(String)
    starttimestamp=Column(DateTime(timezone=True), default=func.now())
    stoptimestamp=Column(DateTime(timezone=True))
  
    def __init__(self, id_user):
          self.id_user=id_user
        
