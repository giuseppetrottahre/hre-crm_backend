from sqlalchemy import Column, String, Integer, Date,Boolean,DateTime,func
from sqlalchemy.dialects.postgresql import UUID

import uuid
from .base import Base,engine


class UserDeleteRequest(Base):
    __tablename__ = 'crm_user_delete_request'
    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    id_user=Column(String)
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
  
    def __init__(self, id_user):
          self.id_user=id_user
        