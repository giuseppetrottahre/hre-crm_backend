
from .base import Session
from .stato import Stato

class StatoController:
    @staticmethod
    def getAll():
        #create a new session
        session = Session()
        #execute-query
        stati = session.query(Stato).all()
        #close session
        session.close()
        #return result if needed
        return(stati)

    def __init__(self):
        pass