from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class ClienteBase(BaseModel):
    nome:str=None
    cognome:str=None
    email:str
    azienda:str=None
    provincia:str=None
    citta:str=None
    cap:str=None
    testoemail:str=None
    filepresentazione:str=None
    inserttimestamp:datetime=None



class ClienteData(ClienteBase):
    id:UUID = Field(default_factory=uuid4)

    class Config:
        orm_mode = True
