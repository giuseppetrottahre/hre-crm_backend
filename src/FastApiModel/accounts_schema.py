from datetime import date
from pydantic import BaseModel

class LoginBase(BaseModel):
    username:str
    password:str=None


class AccountsBase(LoginBase):
    email:str
    permissions:str



class AccountsData(AccountsBase):
    id:int
    inserttimestamp:date
    lastupdatetimestamp:date


    class Config:
        orm_mode = True