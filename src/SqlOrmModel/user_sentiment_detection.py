from sqlalchemy import Column, String, Integer, Date,Boolean,DateTime,func
from sqlalchemy.dialects.postgresql import UUID

import uuid
from .base import Base,engine


class UserSentiment(Base):
    __tablename__ = 'crm_user_sentiment'
    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    id_user=Column(String)
    nome=Column(String)
    secondonome=Column(String)
    cognome=Column(String)
    inspectiontimestamp=Column(DateTime(timezone=True), default=func.now())
    sentiment_detected=Column(String)
  
    def __init__(self, id_user):
          self.id_user=id_user
        
