from sqlalchemy import asc, desc,text,and_,func,update, text
from .base import Session
from .cliente import Cliente
import hashlib

class ClienteController():

    @staticmethod
    def delClient(client_id):
        session = Session()
        clientfilepath=None
        cliente=session.query(Cliente).filter(Cliente.id==client_id).first()
        if cliente:
            clientfilepath=hashlib.md5(cliente.email.encode('utf-8')).hexdigest()
            session.delete(cliente)
        session.commit()
        session.close()
        return clientfilepath


    @staticmethod
    def updClient(client_id,client_data):
        session = Session()
        cliente=session.query(Cliente).filter(Cliente.id==client_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = client_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cliente, key, value)
        baselink="/v1/media/cliente/"
        cliente.filepresentazione=baselink+hashlib.md5(cliente.email.encode('utf-8')).hexdigest()+'/'+cliente.filepresentazione
        cliente.querysearch=func.coalesce(cliente.nome,"")+" "+func.coalesce(cliente.cognome,"")+" "+func.coalesce(cliente.email,"")+" "+func.coalesce(cliente.azienda,"")+" "+func.coalesce(cliente.testoemail,"")
        session.add(cliente)
        session.commit()
        session.refresh(cliente)
        session.close()
        return cliente

    @staticmethod
    def checkExistence(JsonCliente):
       session = Session()
       cliente=Cliente(JsonCliente)
       exists = session.query(Cliente).filter(Cliente.email==cliente.email).first()
       session.commit()
       session.close()
       return(not (exists == None))

    @staticmethod
    def getCliente(cliente_id):
        session = Session()
        cliente=session.query(Cliente).filter(Cliente.id==cliente_id).first()
        session.refresh(cliente)
        session.close()
        return(cliente)

    @staticmethod
    def insert(JsonCliente):
       session = Session()
       cliente=Cliente(JsonCliente)
       session.add(cliente)
       session.commit()
       session.refresh(cliente)
       baselink="/v1/media/cliente/"
       if cliente.filepresentazione is not None:
        cliente.filepresentazione=baselink+hashlib.md5(cliente.email.encode('utf-8')).hexdigest()+'/'+cliente.filepresentazione
       cliente.querysearch=func.coalesce(cliente.nome,"")+" "+func.coalesce(cliente.cognome,"")+" "+func.coalesce(cliente.email,"")+" "+func.coalesce(cliente.azienda,"")+" "+func.coalesce(cliente.testoemail,"")
       session.add(cliente)
       session.commit()
       session.refresh(cliente)
       cid=cliente.id
       session.close()
       return(cid)


    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        cliente=session.query(Cliente)
        totalCount=cliente.count()

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(func.lower(getattr(Cliente, key)).like("%{}%".format(value.lower())))
                elif key in ['provincia']:
                    filters_tuple.append(func.lower(getattr(Cliente, key)).in_((v.lower() for v in value)))  
                else:
                    filters_tuple.append(getattr(Cliente, key) == value)
            cliente=cliente.filter(*filters_tuple)

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                cliente=cliente.order_by(Cliente.__table__.columns[sorting[0]].asc())
            else:
                cliente=cliente.order_by(Cliente.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            cliente=cliente.offset(pagination[0]).limit(pagination[1])

        cliente=cliente.all()
        session.close()
        return (cliente,totalCount) 
    def __init__(self):
        pass