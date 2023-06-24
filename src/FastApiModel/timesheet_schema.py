from datetime import date,datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class TimesheetData(BaseModel):
    id:UUID = Field(default_factory=uuid4)
    id_user:UUID
    nome:str
    secondonome:str
    cognome:str
    starttimestamp:datetime
    stoptimestamp:datetime=None


    class Config:
        orm_mode = True
