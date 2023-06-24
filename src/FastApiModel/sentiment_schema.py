from datetime import date,datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class SentimentData(BaseModel):
    id:UUID = Field(default_factory=uuid4)
    id_user:UUID
    nome:str
    secondonome:str
    cognome:str
    inspectiontimestamp:datetime
    sentiment_detected:str


    class Config:
        orm_mode = True
