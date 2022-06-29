from sqlalchemy import Column, String,DateTime,func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base


class Fornitore(Base):
    __tablename__ = 'crm_fornitore_info'
    id=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome=Column(String)
    cognome=Column(String)
    email=Column(String)
    azienda=Column(String)
    provincia=Column(String)
    citta=Column(String)
    cap=Column(String)
    categoriafornitore=Column(String)
    tipologialocation=Column(String)
    filepresentazione=Column(String)
    querysearch= Column(String,default="") #nome,cognome,email,azienda
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestamp= Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
  
    def __init__(self, obj):
          for property, value in vars(obj).items():
               setattr(self,property.lower(),value)
        