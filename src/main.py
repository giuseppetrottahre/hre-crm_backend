import os,shutil
from typing import List, Type
from fastapi import FastAPI, File,Form,UploadFile,Request, Depends, Response,HTTPException
from sqlalchemy import func

from typing import Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .FastApiModel.fornitore_schema import FornitoreBase,FornitoreData
from .FastApiModel.cliente_schema import ClienteBase,ClienteData
from .FastApiModel.users_schema import UsersBase,UsersData
from .FastApiModel.events_schema import EventsBase,EventsData,EventsUsers
from .FastApiModel.accounts_schema import LoginBase,AccountsBase,AccountsData
from .FastApiModel.timesheet_schema import TimesheetData
from .FastApiModel.sentiment_schema import SentimentData

from .SqlOrmModel.base import Base,engine
from .SqlOrmModel.fornitoreController import FornitoreController
from .SqlOrmModel.clienteController import ClienteController
from .SqlOrmModel.userController import UserController
from .SqlOrmModel.comuneController  import ComuneController
from .SqlOrmModel.statoController  import StatoController
from .SqlOrmModel.backendController  import BackendController
from .SqlOrmModel.eventController import EventController
from .SqlOrmModel.events_usersController import EventUserController
from .SqlOrmModel.timesheetController import TimesheetController 
from .SqlOrmModel.sentimentController import SentimentController 
from .SqlOrmModel.user_timesheet_detection import UserTimesheet
from .SqlOrmModel.user_sentiment_detection import UserSentiment
import json,uuid,hashlib

import typing as t
import secrets
from fastapi.responses import FileResponse
from fastapi.logger import logger


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.encoders import encode_base64
import os
import time
import openpyxl

from . import config as cfg

from .modules.xlsx2Xml import * 
from .modules.recognition import *
from starlette.background import BackgroundTask
#Create all database object

Base.metadata.create_all(engine)

app = FastAPI(debug=True)


#origins = ["*"]

#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=origins,
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)


#disable swagger and Redoc for production
#app = FastAPI(docs_url=None, redoc_url=None)

BasePath="/data"
UtentiPath=BasePath+"/utenti/"
FornitoriPath=BasePath+"/fornitori/"
ClientiPath=BasePath+"/clienti/"
TempPath="/tmp"

#Metodi accessori per geerare il body delle email da inviare in fase di registrazione

def mlSetup():
    users=UserController.getUsersInfoForML()
    setUpImages(users)
    

#Initialize ML info on startup
mlSetup()


#refresh lod on ml info
@app.get("/v1/backend/ml/refresh")
def mlRefresh():
    mlSetup()
    return {"message": "DONE"}


#Clienti
def getClientDescription(id:str,client:ClienteBase):
    message="ID cliente:"+id
    message+="\nNome:"+str(client.nome or '')+" Cognome:"+str(client.cognome or '')
    message+="\nEmail:"+str(client.email or '')
    message+="\nCittà:"+str(client.citta or '')
    message+="\nMessaggio:\n"+str(client.testoemail or '')
    return message
#Fornitori
def getSupplierDescription(id:str,fornitore:FornitoreBase):
    message="ID fornitore:"+id
    message+="\nNome:"+str(fornitore.nome or '')+" Cognome:"+str(fornitore.cognome or '')
    message+="\nEmail:"+str(fornitore.email or '')
    message+="\nCittà:"+str(fornitore.citta or '')
    message+="\nAzienda:\n"+str(fornitore.azienda or '')
    message+="\nCategoria:\n"+str(fornitore.categoriafornitore or '')
    return message
#Uteti Hostess / Steward
def getUserDescription(id:str,hostess_steward:UsersBase):
    message="ID hostess/steward:"+id
    message+="\nNome:"+str(hostess_steward.nome or '')+" Cognome:"+str(hostess_steward.cognome or '')
    message+="\nEmail:"+str(hostess_steward.mail or '')
    message+="\nCittà:"+str(hostess_steward.citta or '')
    return message



#Metodo che invia l'email sfrutta postfix per cui bisogna configurare l'agent in modo opportuno
def send_mail(mail_to, mail_from, subject, text, files, server="localhost"):
    assert type(mail_to) == list
    assert type(files) == list

    msg = MIMEMultipart()
    msg['From'] = mail_from
    msg['To'] = COMMASPACE.join(mail_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    # If Text is HTML, you need to set _subtype = 'html'
         # By default _SUBTYPE = 'plain', ie pure text
    # msg.attach(MIMEText(text, _subtype='html', _charset='utf-8'))
    msg.attach(MIMEText(text, _charset='utf-8'))

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    #smtp = smtplib.SMTP(server)
    #smtp.sendmail(mail_from, mail_to, msg.as_string())
    #smtp.close()


#verifica se una stringa è un uuid valuido
def isUuid(uuidstr):
    try:
        uuid_obj = uuid.UUID(uuidstr)
    except ValueError:
        return False
    return str(uuid_obj) == uuidstr

#in caso di coockie non riconosciuto o sessione scaduta viene restituita una response opportuna dal seguente "builder"
def unhAuthorized():
    response=JSONResponse( content={"message":"ERROR: Accesso non autorizzato"},status_code=401)
    response.headers['Content-Type']='application/json'
    response.headers['Access-Control-Allow-Credentials']='true'
    response.delete_cookie("session_id")
    return response

#controlla se la sessione è attiva e ancora valida 
def isValidSession(request:Request):
    session_id= request.cookies.get("session_id")
    if session_id !='None' :
        return BackendController.checkSession(session_id)
    return False
    


#endpoint per il recupero della lista dei comuni dai form
@app.get("/v1/comune")
def getListaComuni():
    listaComuni=ComuneController.getAll()
    return JSONResponse(content=jsonable_encoder(listaComuni),status_code=200)

#endpoitn per il recupero della lista degli stati dai form
@app.get("/v1/stato")
def getListaStati():
    listaStati=StatoController.getAll()
    return JSONResponse(content=jsonable_encoder(listaStati),status_code=200)



############################################START FORNITORI#################################################################
#costanti generiche di ritorno
SUPPLIER_EXISTS="SUPPLIER_EXISTS"
SUPPLIER_ERRORS="SUPPLIER_ERRORS"
SUPPLIER_SUCCESS="SUPPLIER_SUCCESS"

#Metoo base per l'inserimento di un fornitore
#ritorna:
#l'id (stringa) del fornitore se l'inserimento va  a buon fine
#SUPPLIER_EXISTS se il fornitore esiste già
#SUPPLIER_ERRORS per errori generici (o non viene ritornato nessun id a seguito dell'avvenuto inserimento)

def create_supplier(file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    entity_fornitore=FornitoreBase.parse_raw(jsondata)
    if FornitoreController.checkExistence(entity_fornitore):
        return SUPPLIER_EXISTS
    fid=FornitoreController.insert(entity_fornitore)
    if fid is not None:
        if file is not None:
            savepath=os.path.join(FornitoriPath, hashlib.md5(entity_fornitore.email.encode('utf-8')).hexdigest())
            os.makedirs(savepath, exist_ok=True)
            out_file = open(os.path.join(savepath,entity_fornitore.filepresentazione), "wb") # open for [w]riting as [b]inary
            out_file.write( bytes(file))
            out_file.close()
        send_mail([cfg.receiver_email_address], "Admin", "Registrazione Fornitore", "Un nuovo Fornitore  si è registrato:\n"+getSupplierDescription(str(fid),entity_fornitore), [])
        return str(fid)
    else:
        return SUPPLIER_ERRORS

#endpoint per l'isnerimento di un fornitore da form 
#sostituire i messaggi con dei codici che poi nell pagina del form verranno viusalizzati in una modale 
@app.post("/v1/fornitore")
def form_create_supplier(file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    rsp=create_supplier(file,jsondata)
    if rsp==SUPPLIER_EXISTS:
        return JSONResponse(content={"message":"SUPPLIER_EXISTS"},status_code=250)
    elif rsp==SUPPLIER_ERRORS:
        return JSONResponse(content={"message":"SUPPLIER_ERRORS" },status_code=250)
    else:
         return JSONResponse(content={"message":"SUPPLIER_SUCCESS"},status_code=200)


#recupero list fornitori
@app.get("/v1/backend/suppliers",    response_model=t.List[FornitoreData],
    response_model_exclude_none=False,)
def crm_getAllSuppliers(request:Request,response:Response,filter:str,range:str,sort:str):
    if not isValidSession(request):
         return unhAuthorized()      
    filters=json.loads(filter)
    suppliers,totalCount=FornitoreController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return suppliers


 #recupero singolo fornitore
@app.get("/v1/backend/suppliers/{supplier_id}",response_model=FornitoreData, response_model_exclude_none=True)
def crm_getSupplier( request: Request,supplier_id:str):
    if not isValidSession(request):
         return unhAuthorized()       
    return FornitoreController.getFornitore(supplier_id)  

#inserimento di un fornitore da backoffice
@app.post("/v1/backend/suppliers")
def crm_create_supplier(request:Request,file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized()   
    rsp=create_supplier(file,jsondata)
    if rsp==SUPPLIER_EXISTS:
        return JSONResponse(content={"message":"SUPPLIER_EXISTS"},status_code=250)
    elif rsp==SUPPLIER_ERRORS:
        return JSONResponse(content={"message":"SUPPLIER_ERRORS" },status_code=250)
    else: # int the last else case rsp contains the id of the spplier 
        return JSONResponse(content={"message":"SUPPLIER_SUCCESS","id":str(rsp)},status_code=200)

#aggiornamento singolo fornitore
@app.put("/v1/backend/suppliers/{supplier_id}",response_model=FornitoreData, response_model_exclude_none=True)
def crm_updClient( request: Request,supplier_id:str,file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized() 
    entity_fornitore=FornitoreBase.parse_raw(jsondata)
    if file is not None:
         savepath=os.path.join(FornitoriPath, hashlib.md5(entity_fornitore.email.encode('utf-8')).hexdigest())
         shutil.rmtree(savepath)
         os.makedirs(savepath, exist_ok=True)
         out_file = open(os.path.join(savepath,entity_fornitore.filepresentazione), "wb") # open for [w]riting as [b]inary
         out_file.write( bytes(file))
         out_file.close()
    return FornitoreController.updSupplier(supplier_id,entity_fornitore)


#cancellazione singolo fornitore
@app.delete("/v1/backend/suppliers/{supplier_id}", response_model_exclude_none=True)
def crm_delSupplier( request: Request,supplier_id:str):
    if not isValidSession(request):
         return unhAuthorized()   
    supplierfilepath=FornitoreController.delSupplier(supplier_id)
    if supplierfilepath:
        savepath=os.path.join(FornitoriPath,supplierfilepath)
        if os.path.exists(savepath):
            shutil.rmtree(savepath)
    return JSONResponse(content={"message":"Fornitore eliminato"},status_code=200)
    

############################################END FORNITORI#################################################################

############################################START CLIENTI#################################################################
#costanti generiche di ritorno
CLIENT_EXISTS="CLIENT_EXISTS"
CLIENT_ERRORS="CLIENT_ERRORS"
CLIENT_SUCCESS="CLIENT_SUCCESS"

#Metoo base per l'inserimento di un cliente
#ritorna:
#l'id (stringa) del cliente se l'inserimento va  a buon fine
#CLIENT_EXISTS se il cliente esiste già
#CLIENT_ERRORS per errori generici (o non viene ritornato nessun id a seguito dell'avvenuto inserimento)

def create_client(file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    entity_cliente=ClienteBase.parse_raw(jsondata)
    if ClienteController.checkExistence(entity_cliente):
        return CLIENT_EXISTS
    cid=ClienteController.insert(entity_cliente)
    if cid is not None:
        if file is not None:
            savepath=os.path.join(ClientiPath, hashlib.md5(entity_cliente.email.encode('utf-8')).hexdigest())
            os.makedirs(savepath, exist_ok=True)
            out_file = open(os.path.join(savepath,entity_cliente.filepresentazione), "wb") # open for [w]riting as [b]inary
            out_file.write( bytes(file))
            out_file.close()
        send_mail([cfg.receiver_email_address], "Admin", "Registrazione Cliente", "Un nuovo cliente si è registrato:\n"+getClientDescription(str(cid),entity_cliente), [])
        return str(cid)
    else:
        return CLIENT_ERRORS


#endpoint per l'inserimento di un cliente d form
@app.post("/v1/cliente")
def form_create_client(file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    rsp=create_client(file,jsondata)
    if rsp==CLIENT_EXISTS:
        return JSONResponse(content={"message":"CLIENT_EXISTS"},status_code=250)
    elif rsp==CLIENT_ERRORS:
        return JSONResponse(content={"message":"CLIENT_ERRORS"},status_code=250)
    else:
        return JSONResponse(content={"message":"CLIENT_SUCCESS"},status_code=200)



#recupero lista clienti
@app.get("/v1/backend/clients",    response_model=t.List[ClienteData],
    response_model_exclude_none=False,)
def crm_getAllClients(request:Request,response:Response,filter:str,range:str,sort:str):
    if not isValidSession(request):
         return unhAuthorized()      
    filters=json.loads(filter)
    clients,totalCount=ClienteController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return clients


 #recupero songolo cliente
@app.get("/v1/backend/clients/{client_id}",response_model=ClienteData, response_model_exclude_none=True)
def crm_getClient( request: Request,client_id:str):
    if not isValidSession(request):
         return unhAuthorized()       
    return ClienteController.getCliente(client_id)  


#inserimento di un cliente da backoffice
@app.post("/v1/backend/clients")
def crm_create_client(request:Request,file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized()   
    rsp=create_client(file,jsondata)
    if rsp==CLIENT_EXISTS:
        return JSONResponse(content={"message":"ERROR: Cliente già inserito"},status_code=250)
    elif rsp==CLIENT_ERRORS:
        return JSONResponse(content={"message":"ERROR: Impossibile inserire cliente"},status_code=250)
    else: # in the last case rsp contains the id of the client
        return JSONResponse(content={"message":"SUCCESS: Cliente creato","id":str(rsp)},status_code=200)


#aggiornamento singolo cliente
@app.put("/v1/backend/clients/{client_id}",response_model=ClienteData, response_model_exclude_none=True)
def crm_updClient( request: Request,client_id:str,file: Optional[bytes] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized() 
    entity_cliente=ClienteBase.parse_raw(jsondata)
    if file is not None:
         savepath=os.path.join(ClientiPath, hashlib.md5(entity_cliente.email.encode('utf-8')).hexdigest())
         shutil.rmtree(savepath)
         os.makedirs(savepath, exist_ok=True)
         out_file = open(os.path.join(savepath,entity_cliente.filepresentazione), "wb") # open for [w]riting as [b]inary
         out_file.write( bytes(file))
         out_file.close()
    return ClienteController.updClient(client_id,entity_cliente)

#cancellazione singolo cliente
@app.delete("/v1/backend/clients/{client_id}", response_model_exclude_none=True)
def crm_delClient( request: Request,client_id:str):
    if not isValidSession(request):
         return unhAuthorized()   
    clientfilepath=ClienteController.delClient(client_id)
    if clientfilepath:
        savepath=os.path.join(ClientiPath,clientfilepath)
        if os.path.exists(savepath):
            shutil.rmtree(savepath)
    return JSONResponse(content={"message":"Cliente eliminato"},status_code=200)

############################################END CLIENTI#################################################################
############################################START EVENTI################################################################

#recupero list eventi
@app.get("/v1/backend/events",    response_model=t.List[EventsData],
    response_model_exclude_none=False,)
def crm_getAllEvents(request:Request,response:Response,filter:str,range:str,sort:str):
    if not isValidSession(request):
         return unhAuthorized()      
    filters=json.loads(filter)
    events,totalCount=EventController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return events



#creazione evento
@app.post("/v1/backend/events", response_model=EventsData, response_model_exclude_none=True)
def crm_create_event(  request: Request,
    event: EventsBase):
    if not isValidSession(request):
         return unhAuthorized()      
    return EventController.insert(event)


#richiesa singolo evento
@app.get("/v1/backend/events/{event_id}",response_model=EventsData, response_model_exclude_none=True)
def crm_getEvent( request: Request,event_id:str):
    if not isValidSession(request):
         return unhAuthorized()      
    return EventController.getEvent(event_id)


#cancellazione singolo evento
@app.delete("/v1/backend/events/{event_id}",response_model=EventsData, response_model_exclude_none=True)
def crm_delEvent( request: Request,event_id:str):
    if not isValidSession(request):
         return unhAuthorized()      
    EventController.delEvent(event_id)
    return JSONResponse(content={"message":"SUCCESS: Utente eliminato"},status_code=200)

   
#aggiornamento singolo evento
@app.put("/v1/backend/events/{event_id}",response_model=EventsData, response_model_exclude_none=True)
def crm_updEvent( request: Request,event_id:str,event:EventsBase):
    if not isValidSession(request):
         return unhAuthorized()      
    return EventController.updEvent(event_id,event)

############################################END EVENTI#################################################################
############################################START ACCOUNT#################################################################

#recupero list accounts
@app.get("/v1/backend/accounts",    response_model=t.List[AccountsData],
    response_model_exclude_none=False,)
def crm_getAllAccounts(request:Request,response:Response,filter:str,range:str,sort:str):
    if not isValidSession(request):
         return unhAuthorized()      
    filters=json.loads(filter)
    events,totalCount=BackendController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return events

#recupero  account
@app.get("/v1/backend/accounts/{account_id}",response_model=AccountsData,
    response_model_exclude_none=False)
def crm_getAccount(request:Request,account_id:str):
    if not isValidSession(request):
         return unhAuthorized()       
    return BackendController.getAccount(account_id)  


#creazione account
@app.post("/v1/backend/accounts", response_model=AccountsData, response_model_exclude_none=True)
def crm_create_account(  request: Request,   account: AccountsBase):
    if not isValidSession(request):
         return unhAuthorized()
    if BackendController.checkAccount(account.username):
        return JSONResponse(content={"message":"User already exists"},status_code=302)
    pwdtmp=secrets.token_urlsafe(32)     
    account.password=hashlib.md5(pwdtmp.encode('utf-8')).hexdigest()
    send_mail([account.email], "Admin", "Password primo accesso", "Questa è la tua password temporanea per il primo accesso: "+pwdtmp, [])
    return BackendController.insert(account)

#cancellazione singolo account
@app.delete("/v1/backend/accounts/{account_id}", response_model_exclude_none=True)
def crm_delAccount( request: Request,account_id:str):
    if not isValidSession(request):
         return unhAuthorized()      
    return BackendController.delAccount(account_id)

   
#aggiornamento singolo account
@app.put("/v1/backend/accounts/{account_id}",response_model=AccountsData, response_model_exclude_none=True)
def crm_updAccount( request: Request,account_id:str,account:AccountsBase):
    if not isValidSession(request):
         return unhAuthorized()      
    return BackendController.updAccount(account_id,account)
############################################END ACCOUNT #################################################################
REQUEST_TAKING_IN_CHARGE="REQUEST_TAKING_IN_CHARGE" #richiesta di cancellazione presa in carico
USER_NOT_FOUND="USER_NOT_FOUND" #utente non trovato
USER_EXISTS="USER_EXISTS" #l'utente eiste già
USER_SUCCESS="USER_SUCCESS" #utente creato con successo
USER_ID_NOT_VALID="USER_ID_NOT_VALID" #id utente non valido
EVENT_ID_NOT_VALID="EVENT_ID_NOT_VALID" #id evento non valido
EVENT_NOT_FOUND="EVENT_NOT_FOUND" #evento non valido
PROPOSAL_CONFIRMED="PROPOSAL_CONFIRMED" #proposal confirmed success
PROPOSAL_ERROR="PROPOSAL_ERROR"  #proposal error
#controlla se un utente è inserito
@app.get("/v1/utente/check/{codicefiscale}")
def form_check_user_existence(codicefiscale:str):
    exists=UserController.checkCf(codicefiscale)
    return JSONResponse(content={"result": jsonable_encoder(exists)},status_code=200)


#richiesa cancellazione utente
@app.get("/v1/utente/delete/request/{codicefiscale}")
def form_erase_user_request(codicefiscale:str):
    result=UserController.delete_request(codicefiscale)
    if result is not None:
        user_email=UserController.getEmail(codicefiscale)
        #logger.warning("/v1/utente/delete/action/"+str(result))
        dlink="https://job.prc-srl.com/v1/utente/delete/action/"+str(result)
        send_mail([user_email], "Admin", "Conferma Cancellazione", "clicca sul seguente link per eliminare i tuoi dati: "+dlink, [])

        return JSONResponse(content={"message":REQUEST_TAKING_IN_CHARGE},status_code=200)
    else:
        return JSONResponse(content={"message":USER_NOT_FOUND},status_code=250)



#esecuzione cancellazione utente
@app.get("/v1/utente/delete/action/{delete_req_id}")
def form_erase_user_apply(delete_req_id:str):
    if(delete_req_id):
        userid=UserController.remove(delete_req_id)
        if userid is not None:
            savepath=os.path.join(UtentiPath,str(userid).upper())
            if os.path.exists(savepath):
                shutil.rmtree(savepath)
            return JSONResponse(content={"result":"SUCCESS: Utente eliminato"},status_code=200)
        else:
            return JSONResponse(content={"error_msg":"ERROR: Impossibile eliminare l'utente"},status_code=250)


async def create_user(jsondata:str = Form(...),files: Optional[List[UploadFile]] = File(None)):
    entity_utente=UsersBase.parse_raw(jsondata)
    userid=UserController.insert(entity_utente)
    if userid is not None:
        savepath=os.path.join(UtentiPath, entity_utente.codicefiscale.upper())
        os.makedirs(savepath, exist_ok=True)
        if files is not None:
         for file in files:
            with open(os.path.join(savepath,file.filename), 'wb') as document:
                content = await file.read()
                document.write(content)
                document.close()   
        send_mail([cfg.receiver_email_address], "Admin", "Registrazione nuovo candidato", "Nuovo candidato registrata/o:\n"+getUserDescription(str(userid),entity_utente), [])
        return userid
    else:
        return USER_EXISTS

#endpoint per l'inerimento di un utente
@app.post("/v1/utente")
async def form_create_user(jsondata:str = Form(...),files: Optional[List[UploadFile]] = File(None)):
    rsp=await create_user(jsondata,files)
    if rsp==USER_EXISTS:
        return JSONResponse(content={"message":USER_EXISTS},status_code=250)
    else:
        return JSONResponse(content={"message":USER_SUCCESS},status_code=200)


#endpoint per l'inerimento di un utente
@app.get("/v1/candidatura/{eventid}/{userid}")
def  form_confirmProposal(response:Response,eventid:str,userid:str):
    if not eventid or not userid:
        return JSONResponse(content={"message":"Bad request"},status_code=400)
    if not isUuid(eventid):
         return JSONResponse(content={"message":EVENT_ID_NOT_VALID},status_code=200)
    if not isUuid(userid):
         return JSONResponse(content={"message":USER_ID_NOT_VALID},status_code=200)

    eventExists=EventController.checkEventid(eventid)
    if not eventExists:
        return JSONResponse(content={"message":EVENT_NOT_FOUND},status_code=200)

    userExists=UserController.checkUserid(userid)
    if not userExists:
        return JSONResponse(content={"message":USER_NOT_FOUND},status_code=200)

#    candidacyExists=EventController.checkCandidacy(eventid,userid)
#    if candidacyExists:
#        return JSONResponse(content={"message":"SUCCESS: Candidatura già esistente"},status_code=200)

    eventdata=EventsUsers(event_id=eventid,user_id=userid)
  #  candidacy=EventController.manageCandidacy("ADD",eventdata)
    candidacy=EventUserController.confirmProposal(eventdata)
    if candidacy:
       response=JSONResponse(content={"message":PROPOSAL_CONFIRMED},status_code=200)
    else:
       response=JSONResponse(content={"message":PROPOSAL_ERROR},status_code=400) 
    return response

#endpoint per il login di un utente
@app.post("/v1/backend/login")
def crm_login(response:Response,entity_login:LoginBase):
    user_session=BackendController.login(entity_login)
    
    if user_session != (None,None,None,None):
           # response.headers['Access-Control-Allow-Origin']='*'
             #user_session[1]=user_id, user_sesion[2]=permissions user_session[3]=firstlogin
            if user_session[3] == True:
                response=JSONResponse(content={"user_id":user_session[1],"permissions":"firstlogin"},status_code=200)
            else:
                response=JSONResponse(content={"user_id":user_session[1],"permissions":user_session[2]},status_code=200)
            response.set_cookie(key="session_id",value=user_session[0],httponly=True) #user_session[0]=session_id
  #          return JSONResponse(content={"message":jsonable_encoder(session_id)},status_code=200)
            return response
    else:
          return JSONResponse(content={"error_msg":"Impossibile effettuare il login"},status_code=401)


#endpoint per il reset password di un utente 
@app.get("/v1/backend/resetpwd/{username}")
def crm_resetpwd(response:Response,username:str):

    pwdtmp = secrets.token_urlsafe(32)
    user_email=BackendController.resetPwd(username,pwdtmp)
    
    if user_email is not None:
           # response.headers['Access-Control-Allow-Origin']='*'
            send_mail([user_email], "Admin", "Reset password", "Questa è la tua nuova password temporanea: "+pwdtmp, [])
            response=JSONResponse(content={"message":"Password resettata"},status_code=200)
            return response
    else:
          return JSONResponse(content={"error_msg":"Impossibile effettuare il login"},status_code=401)

#endpoint per il reset password di un utente 
@app.post("/v1/backend/changepwd")
def crm_changepwd(request:Request,response:Response,entity_login:LoginBase):
    if not isValidSession(request):
        return unhAuthorized()   
    status=BackendController.changePwd(entity_login)
    if status == True:
        response=JSONResponse(content={"message":"Password settata"},status_code=200)
    else:
        response=JSONResponse(content={"error_msg":"Impossibile settare passowrd"},status_code=401)
    return response      




#endpoint per il logout di un utente
@app.get("/v1/backend/logout")
def crm_logout(response:Response,request:Request):
 #   if not isValidSession(request):
 #        return unhAuthorized()   
    session_id= request.cookies.get("session_id")
    BackendController.logout(session_id)
    response=JSONResponse(content={"message":"SUCCESS"},status_code=200)
    response.delete_cookie("session_id")
    return response
#    if session_id is not None:
#           # response.headers['Access-Control-Allow-Origin']='*'
#            response=JSONResponse(content={"message":"setcookie"},status_code=200)
#            response.set_cookie(key="session_id",value=session_id,httponly=True)
#  #          return JSONResponse(content={"message":jsonable_encoder(session_id)},status_code=200)
#            return response
#    else:
#          return JSONResponse(content={"error_msg":"Impossibile effettuare il login"},status_code=401)

@app.get("/v1/backend/users",    
    response_model=t.List[UsersData],
    response_model_exclude_none=False,)
def crm_getAll(response:Response,filter:str,range:str,sort:str,request:Request):

    if not isValidSession(request):
        return unhAuthorized()   
 
    filters=json.loads(filter)
     #Pagination
    #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
    # and cast to int thw two numbers
   # offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
   # pagination=(offset,r_end-offset)  #offset=pagenumber r_end-offset=number of record

    #Sorting
    #sort is a string array for example sort=["name","ASC|DESC"]
    #sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
    users,totalCount=UserController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return users

#richiesa singolo user
@app.get("/v1/backend/users/{user_id}",response_model=UsersData, response_model_exclude_none=True)
def crm_getUser( request: Request,user_id:str):
    if not isValidSession(request):
         return unhAuthorized()   
    return UserController.getUser(user_id)


#aggiornamento singolo utente
@app.put("/v1/backend/users/{user_id}",response_model=UsersData, response_model_exclude_none=True)
async def crm_updUser( request: Request,user_id:str,files: Optional[List[UploadFile]] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized() 
    entity_utente=UsersBase.parse_raw(jsondata)
    #lista dei nuovi file
    fileslistToUpdate=[entity_utente.filenameinputcv,
    entity_utente.filenameinputprofiloimg ]
    if files is not None:
        savepath=os.path.join(UtentiPath, entity_utente.codicefiscale.upper())  
        #lista file attuali contenuti nella folder 
        onlyfiles = [f for f in os.listdir(savepath) if os.path.isfile(os.path.join(savepath, f))]      
        for f in onlyfiles:
            #per ogni vecchio file non contenuto nella lista, lo elimino 
            if f not in fileslistToUpdate:
                os.remove(os.path.join(savepath, f))
         #aggiungo i nuovi file       
        for file in files:
                with open(os.path.join(savepath,file.filename), 'wb') as document:
                    content = await file.read()
                    document.write(content)
                    document.close()                  
    return UserController.updUser(user_id,entity_utente) 





#cancellazione singolo user da rivedere il return credo ritori un oggetto vuoto.sostituire con true o false 
@app.delete("/v1/backend/users/{user_id}",response_model=UsersData, response_model_exclude_none=True)
def crm_delUser( request: Request,user_id:str):
    if not isValidSession(request):
         return unhAuthorized()      
         #recuperare il codice fiscale dallo userid e poi eliminare il path
    codicefiscale=UserController.getCf(user_id)   
    if os.path.exists(os.path.join(UtentiPath,codicefiscale)):
        shutil.rmtree(UtentiPath+codicefiscale)
    UserController.delUser(user_id)
    return JSONResponse(content={"message":"SUCCESS: Utente eliminato"},status_code=200)


#endpoint per l'isnerimento di un cliente da backend
@app.post("/v1/backend/users")
async def crm_create_user(request:Request,files: Optional[List[UploadFile]] = File(None),jsondata:str = Form(...)):
    if not isValidSession(request):
         return unhAuthorized()   
    rsp=await create_user(jsondata,files)
    if rsp==USER_EXISTS:
        return JSONResponse(content={"message":"ERROR:Utente già inserito"},status_code=250)
    else: # in this case rsp contains the id of the user 
        return JSONResponse(content={"message":"SUCCESS: utente creato","id":str(rsp)},status_code=200)



####################################UTENTI################################################################



#recupero file
@app.get("/v1/media/{category}/{categorypath}/{filename}", response_model_exclude_none=False,)
async def getMediaFile(request:Request,category:str,categorypath:str,filename:str)-> FileResponse:
    if not isValidSession(request):
         return unhAuthorized()      
    if category.upper() not in ["UTENTE","FORNITORE","ARTISTA","CLIENTE"]:
                raise HTTPException(status_code=404, detail="Operation not supported")
    folderPath=""
    if category.upper()=="UTENTE":folderPath=UtentiPath
    if category.upper()=="FORNITORE":folderPath=FornitoriPath
    if category.upper()=="ARTISTA":folderPath=ArtistiPath
    if category.upper()=="CLIENTE":folderPath=ClientiPath
    return FileResponse(f'{folderPath}/{categorypath}/{filename}')
    

@app.get("/v1/backend/events_users", #response_model=t.List[AccountsData],
    response_model_exclude_none=False,)
def getEventsUsers(request:Request,response:Response,filter:str,range:str,sort:str):
    if not isValidSession(request):
         return unhAuthorized()    
    filters=json.loads(filter)
    eventsusers,totalCount=EventUserController.getUsersList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return eventsusers

@app.post("/v1/backend/envets_users/propose",  response_model_exclude_none=False,)
def proposeEvent(request:Request,jsondata:EventsUsers):
    if not isValidSession(request):
         return unhAuthorized()      
    (proposal,email)=EventUserController.proposeEventUser(jsondata)
    send_mail([email], "Admin", "Notifica Evento", proposal, [])
    return JSONResponse(content={"message":"SUCCESS: Notifica evento inviata"},status_code=200)

def sql_query_to_csv(query_output, columns_to_exclude=""):
 rows = query_output
 columns_to_exclude = set(columns_to_exclude)

 #create list of column names  
 column_names = [i for i in rows[0].__dict__]
 for column_name in columns_to_exclude:
  column_names.pop(column_names.index(column_name))

 #add column titles to csv
 column_names.sort()
 csv = ", ".join(column_names) + "\n"

 #add rows of data to csv
 for row in rows:
  for column_name in column_names:
   if column_name not in columns_to_exclude:
    data = str(row.__dict__[column_name])
    #Escape (") symbol by preceeding with another (")
    data.replace('"','""')
    #Enclose each datum in double quotes so commas within are not treated as separators
    csv += '"' + data + '"' + ","

  csv += "\n"
 return csv


@app.get("/v1/backend/export", response_model_exclude_none=False,)
async def getXlsExport(request:Request,response:Response,filter:str)-> FileResponse:
    if not isValidSession(request):
         return unhAuthorized()    
    filters=json.loads(filter)
    users,totalCount=UserController.getList(filters,None,None) #range:str,sort:str
    logger.info("Export "+str(totalCount)+" of users")
    csv=sql_query_to_csv(users,["_sa_instance_state"]).split("\n")

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in csv:
        if row !="":
            sheet.append(row.split(","))
    timestr = time.strftime("%Y%m%dT%H%M%S")    
    filePathXls=TempPath+"/users_"+timestr+".xlsx"
    workbook.save(filePathXls)
    return FileResponse(f'{filePathXls}')


def cleanFiles(filePathList):
    for f in filePathList:
        if os.path.exists(f):
            os.remove(f);

#this method accept a Excel file and then get back an xml file
@app.post("/v1/backend/final_balance")
def generateXmlFromExcel(request:Request,filexls: Optional[bytes] = File(None), jsondata:str=Form(...))->FileResponse:
    if not isValidSession(request):
          return unhAuthorized()
    json_data = json.loads(jsondata)
    if filexls is not None:
        inputFileName=os.path.join(TempPath,json_data['fileconsuntivazioneexcel'])
        out_file = open(inputFileName, "wb") # open for [w]riting as [b]inary
        out_file.write( bytes(filexls))
        out_file.close()
        outputFileName=getXml(inputFileName)
        return  FileResponse(f'{outputFileName}', background=BackgroundTask(cleanFiles, [inputFileName,outputFileName]))       
    else:
        return   JSONResponse(content={"message":"Internal Error contact adinistrator" },status_code=250)


#this method accept a Excel file and then get back an xml file
@app.get("/v1/backend/final_balance_log")
def generateXmlFromExcel(request:Request)->FileResponse:
    if not isValidSession(request):
          return unhAuthorized()
    outputFileName='/tmp/import.log'
    if os.path.isfile(outputFileName):
        return  FileResponse(f'{outputFileName}')
    else:
        return   JSONResponse(content={"message":"Internal Error or File does not exists" },status_code=250)




#endpoint for Photo Upload
@app.post("/v1/backend/tnotification")
def timesheet_notification(fileImg:UploadFile=File(...)):
    logger.info("[timesheet_notification] [filename:"+fileImg.filename+"]")
    message=""
    try:
        contents=fileImg.file.read()
        fileName=TempPath+"/"+fileImg.filename
        with open(fileName,'wb') as f:
            f.write(contents)
    except Exception:
        logger.error("[timesheet_notification] [filename:"+fileImg.filename+"] [UPLOAD FAILED]")
        return {"message":"Error uploading file"}
    finally:
        fileImg.file.close()
    identity_matched=analyze(fileName) #analyze(fileName,cfg.csvInfoPath)
    if identity_matched[0] != "Unknown":
        user_id=UserController.checkCf(identity_matched[2])
        logger.info('prova:'+str(user_id))
        if user_id:
            timesheet_id=TimesheetController.getSingleRowOpenForUserId(user_id)
            logger.info('provat:'+str(timesheet_id))
            if timesheet_id is None:
                user=UserController.getUser(user_id)
                timesheet_row=UserTimesheet(user_id)
                timesheet_row.nome=user.nome
                timesheet_row.secondonome=user.secondonome
                timesheet_row.cognome=user.cognome
                TimesheetController.insert(timesheet_row)
                message={"identity":identity_matched[0],"status":"IN"}
            else:
                TimesheetController.closeTimeSheet(timesheet_id)
                message={"identity":identity_matched[0],"status":"OUT"}
        else:
            message= {"error":"User nont found for CF:"+identity_matched[2]}
    else:
        message={"identity":"UNKNOW"}
    logger.info("[timesheet_notification] [filename:"+fileImg.filename+"]["+str(message)+"]")
    os.remove(fileName)
    return message

#endpoint for Photo Upload
@app.post("/v1/backend/snotification")
def sentiment_notification(fileImg:UploadFile=File(...)):
    logger.info("[sentiment_notification] [filename:"+fileImg.filename+"]")
    message=""
    try:
        contents=fileImg.file.read()
        fileName=TempPath+"/"+fileImg.filename
        with open(fileName,'wb') as f:
            f.write(contents)
    except Exception:
        logger.error("[sentiment_notification] [filename:"+fileImg.filename+"] [UPLOAD FAILED]")
        return {"message":"Error uploading file"}
    finally:
        fileImg.file.close()
        exifOrientation(fileName)
    identity_matched=analyze(fileName) #analyze(fileName,cfg.csvInfoPath)
    if identity_matched[0] != "Unknown":
        user_id=UserController.checkCf(identity_matched[2])
        if user_id:
                user=UserController.getUser(user_id)
                sentiment_row=UserSentiment(user_id)
                sentiment_row.nome=user.nome
                sentiment_row.secondonome=user.secondonome
                sentiment_row.cognome=user.cognome
                sentiment_analysis=sentiment_detection(fileName)
                sentiment=sentiment_analysis[0]['dominant_emotion']
                sentiment_row.sentiment_detected=sentiment
                SentimentController.insert(sentiment_row)
                message={"identity":identity_matched[0],"sentiment":sentiment}
        else:
            message={"error":"User nont found for CF:"+identity_matched[2]}
    else:
        message={"identity":"UNKOWN"}
    logger.info("[sentiment_notification] [filename:"+fileImg.filename+"]["+str(message)+"]")
    os.remove(fileName)
    return message

#
#mask detection
@app.post("/v1/backend/maskdetection")
def mask_notification(fileImg:UploadFile=File(...)):
    logger.info("[mask_notification] [filename:"+fileImg.filename+"]")
    try:
        contents=fileImg.file.read()
        fileName=TempPath+"/"+fileImg.filename
        with open(fileName,'wb') as f:
              f.write(contents)
    except Exception:
         logger.error("[mask_notification] [filename:"+fileImg.filename+"] [UPLOAD FAILED]")
         return {"message":"Error uploading file"}
    finally:
        fileImg.file.close()
    
    m_detected= mask_detection(fileName)
    logger.info("[mask_notification] [filename:"+fileImg.filename+"][MASK:"+str(m_detected)+"]")
    os.remove(fileName)
    return {"Mask":m_detected}



####TIMESHEET####
@app.get("/v1/backend/timesheet",
    response_model=t.List[TimesheetData],
    response_model_exclude_none=False,)
def get_crm_timesheet(response:Response,filter:str,range:str,sort:str,request:Request):
    if not isValidSession(request):
        return unhAuthorized()

    filters=json.loads(filter)
    timesheet,totalCount=TimesheetController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return timesheet


#richiesa singolo row
@app.get("/v1/backend/timesheet/{timesheet_id}",response_model=TimesheetData, response_model_exclude_none=True)
def get_crm_timesheet_row( request: Request,timesheet_id:str):
    if not isValidSession(request):
         return unhAuthorized()
    return TimesheetController.getSingleRow(timesheet_id)

@app.put("/v1/backend/timesheet/{timesheet_id}",response_model=TimesheetData, response_model_exclude_none=True)
def update_crm_timesheet(request:Request,timesheet_id:str,jsondata:str=Form(...)):
    if not isValidSession(request):
         return unhAuthorized()
    timesheet_row=TimesheetData.parse_raw(jsondata)
    return TimesheetController.updateSingleRow(timesheet_id,timesheet_row)

@app.delete("/v1/backend/timesheet/{timesheet_id}")
def delete_crm_timesheet(request:Request,timesheet_id:str):
    if not isValidSession(request):
         return unhAuthorized()
    TimesheetController.remove_timesheet(timesheet_id)
    return JSONResponse(content={"message":"SUCCESS: Riga eliminata"},status_code=200)

###SENTIMENT####
@app.get("/v1/backend/sentiment",
    response_model=t.List[SentimentData],
    response_model_exclude_none=False,)
def get_crm_sentiment(response:Response,filter:str,range:str,sort:str,request:Request):
    if not isValidSession(request):
        return unhAuthorized()

    filters=json.loads(filter)
    sentiment,totalCount=SentimentController.getList(filters,range,sort)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Range'
    response.headers["Content-Range"] = f"posts 0-9/{totalCount}"
    return sentiment



#richiesa singolo row
@app.get("/v1/backend/sentiment/{sentiment_id}",response_model=SentimentData, response_model_exclude_none=True)
def get_crm_timesheet_row( request: Request,sentiment_id:str):
    if not isValidSession(request):
         return unhAuthorized()
    return SentimentController.getSingleRow(sentiment_id)


@app.put("/v1/backend/sentiment/{sentiment_id}",response_model=SentimentData, response_model_exclude_none=True)
def update_crm_sentiment(request:Request,sentiment_id:str,jsondata:str=Form(...)):
    if not isValidSession(request):
         return unhAuthorized()
    sentiment_row=SentimentData.parse_raw(jsondata)
    return SentimentController.updateSingleRow(sentiment_id,sentiment_row)


@app.delete("/v1/backend/sentiment/{sentiment_id}")
def delete_crm_sentiment(request:Request,sentiment_id:str):
    if not isValidSession(request):
         return unhAuthorized()
    TimesheetController.remove_sentiment(sentiment_id)
    return JSONResponse(content={"message":"SUCCESS: Riga eliminata"},status_code=200)
