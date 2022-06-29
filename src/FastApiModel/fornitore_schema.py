from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime 


class FornitoreBase(BaseModel):
    nome:str=None
    cognome:str=None
    email:str
    azienda:str=None
    provincia:str=None
    citta:str=None
    cap:str=None
    categoriafornitore:str=None
    tipologialocation:str=None
    filepresentazione:str=None
    inserttimestamp:datetime=None


class FornitoreData(FornitoreBase):
    id:UUID = Field(default_factory=uuid4)

    class Config:
        orm_mode = True
