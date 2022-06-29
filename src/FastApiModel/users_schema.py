from datetime import date,datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import List
from .events_schema import EventsBase,EventsData

class UsersBase(BaseModel):
    nome:str
    secondonome:str=None
    cognome:str
    mail:str
    genere:str
    cellulare:str
    telefono:str=None
    codicefiscale:str
    indirizzodomicilio:str
    provincia:str
    citta:str
    cap:str
    nazionedinascita:str
    provinciadinascita:str
    cittadinascita:str
    note:str=None
    fblink:str=None
    instalink:str=None
    datadinascita:date
    #STEP 2
    titolodistudi:str=None
    annodiconseguimento:str=None
    notepersonali:str=None
    istituto:str=None
    votazione:str=None
    inglese:str
    francese:str=None
    tedesca:str=None
    spagnola:str=None
    altrelingue:str=None
    #STEP 3
    haccp:bool=False
    primosoccorso:bool=False
    antincendio:bool=False
    tesserinoaeroporto:bool=False
    brevetto:bool=False
    tesserinosicurezza:bool=False
    automunito:bool=False
    patenteauto:bool=False
    #STEP 4
    filenameinputcv:str
    filenameinputprofiloimg:str=None
    #Backend Added
    regione:str=None
    stato:str=None    
    valutazione:str=None
    inserttimestamp:datetime=None

class UsersData(UsersBase):
    id:UUID = Field(default_factory=uuid4)

  
    class Config:
        orm_mode = True
