from datetime import date
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import List


class EventsUsers(BaseModel):
    event_id:UUID
    user_id:UUID

class EventsBase(BaseModel):
    nomeevento:str
    datainizio:date=None 
    datafine:date=None
    attivo:bool=None
    descrizione:str=None
    numerominimocandidati:int=None
    numeromassimocandidati:int=None
    urlcandidature:str=None


class EventsData(EventsBase):
    id:UUID = Field(default_factory=uuid4)
    linkcandidaturautenti:str
    linkcandidaturaweb:str


    class Config:
        orm_mode = True