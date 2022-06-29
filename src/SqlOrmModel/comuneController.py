
from .base import Session
from .comune import Comune

class ComuneController:
    @staticmethod
    def getAll():
        #create a new session
        session = Session()
        #execute-query
        comuni = session.query(Comune).all()
        #close session
        session.close()
        #return result if needed
        return(comuni)

    def __init__(self):
        pass