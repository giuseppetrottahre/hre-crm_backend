from sqlalchemy import Column, String, Integer, Date,Boolean,DateTime,func,Text,Index,ForeignKey,Table
from sqlalchemy.orm import column_property,relationship
from sqlalchemy.dialects.postgresql import UUID,ARRAY
import uuid
from .base import Base

class EventsUsers(Base):
    __tablename__ = 'crm_events_users'
    id=Column(Integer, primary_key=True)
    event_id=Column(ForeignKey('crm_event.id'))
    user_id=Column(ForeignKey('crm_user_info.id'))
    status=Column(String)
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestamp= Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
    users = relationship("User",lazy='subquery')
    events = relationship("Event", lazy='subquery')

     

 
  
    #def __init__(self, obj):
    #       for property, value in vars(obj).items():
    #           setattr(self,property.lower(),value)


#per l'indice eseguire psql:
#\c
#CREATE EXTENSION pg_trgm;
class Event(Base):
    __tablename__ = 'crm_event'
    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    nomeevento=Column(String, nullable=False)
    datainizio=Column(Date)
    datafine=Column(Date)
    attivo=Column(Boolean, default=False)
    descrizione=Column(String,default="")
    numerominimocandidati=Column(Integer)
    numeromassimocandidati=Column(Integer)
    urlcandidature=Column(String)
    linkcandidaturautenti=Column(String,default="")
    linkcandidaturaweb=Column(String,default="")
    querysearch= Column(String,default="")
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestamp= Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
    #users=relationship("User",secondary='crm_events_users',backref="events",lazy='subquery')
    users_id=Column(ARRAY(UUID))

    __table_args__ = (Index('ix__event__querysearch',
          'querysearch', postgresql_using='gin',      
          postgresql_ops={
          'querysearch': 'gin_trgm_ops',
      }),Index('ix__event__users_id',
          'users_id', postgresql_using='gin',      
          postgresql_ops={
          'querysearch': 'gin_trgm_ops',
      }),
      )
  
    def __init__(self, obj):
           for property, value in vars(obj).items():
               setattr(self,property.lower(),value)

           
#per l'indice eseguire psql:
#\c
#CREATE EXTENSION pg_trgm;

class User(Base):
    __tablename__ = 'crm_user_info'
    id = Column(UUID(as_uuid=True), primary_key=True,  default=uuid.uuid4)
    #STEP 1
    nome=Column(String)
    secondonome=Column(String)
    cognome=Column(String)
    mail=Column(String)
    genere=Column(String)
    cellulare=Column(String)
    telefono=Column(String)
    codicefiscale=Column(String)
    indirizzodomicilio=Column(String)
##NEW BACKEND
    stato=Column(String,default="Nuovo")
    valutazione=Column(String,default="")
    regione=Column(String)
##STOP BACKEND    
    provincia=Column(String)
    citta=Column(String)
    cap=Column(String)
    nazionedinascita=Column(String)
    provinciadinascita=Column(String)
    cittadinascita=Column(String)
    note=Column(String)
    fblink=Column(String)
    instalink=Column(String)
    datadinascita=Column(Date)
    #STEP 2
    titolodistudi=Column(String)
    annodiconseguimento=Column(String)
    notepersonali=Column(String)
    istituto=Column(String)
    votazione=Column(String)
    inglese=Column(String)
    francese=Column(String)
    tedesca=Column(String)
    spagnola=Column(String)
    altrelingue=Column(String)
    #STEP 3
    haccp=Column(Boolean)
    primosoccorso=Column(Boolean)
    antincendio=Column(Boolean)
    tesserinoaeroporto=Column(Boolean)
    brevetto=Column(Boolean)
    tesserinosicurezza=Column(Boolean)
    automunito=Column(Boolean)
    completonero=Column(Boolean)
    scarpanera=Column(Boolean)
    tubinoneroelegante=Column(Boolean)   
    tailleurneropantalone=Column(Boolean) 
    tailleurnerogonna=Column(Boolean) 
    scarpedecolletenere=Column(Boolean) 
    patenteauto=Column(Boolean)
    #STEP 4
    filenameinputcv=Column(String)
    filenameinputprofiloimg=Column(String)
    querysearch= Column(String,default="")
    inserttimestamp=Column(DateTime(timezone=True), default=func.now())
    lastupdatetimestamp= Column(DateTime(timezone=True), default=func.now(),onupdate=func.now())
    #events=relationship("EventsUsers", back_populates="users")
    events_id=Column(ARRAY(UUID))

    __table_args__ = (Index('ix__user__querysearch',
          'querysearch', postgresql_using='gin',      
          postgresql_ops={
          'querysearch': 'gin_trgm_ops',
      }),Index('ix__user__events_id',
          'events_id', postgresql_using='gin',      
          postgresql_ops={
          'querysearch': 'gin_trgm_ops',
      }),
      )


  
    def __init__(self, obj):
           for property, value in vars(obj).items():
               setattr(self,property.lower(),value)
