from sqlalchemy import asc, desc,text,and_,func,update, text
from .base import Session
from .fornitore import Fornitore
import hashlib

class FornitoreController():

    @staticmethod
    def delSupplier(supplier_id):
        session = Session()
        supplierfilepath=None
        supplier=session.query(Fornitore).filter(Fornitore.id==supplier_id).first()
        if supplier:
            supplierfilepath=hashlib.md5(supplier.email.encode('utf-8')).hexdigest()
            session.delete(supplier)
        session.commit()
        session.close()
        return supplierfilepath

    @staticmethod
    def checkExistence(JsonFornitore):
       session = Session()
       fornitore=Fornitore(JsonFornitore)
       exists = session.query(Fornitore).filter(Fornitore.email==fornitore.email).first()
       session.commit()
       session.close()
       return(not (exists == None))

    @staticmethod
    def getFornitore(supplier_id):
        session = Session()
        fornitore=session.query(Fornitore).filter(Fornitore.id==supplier_id).first()
        session.refresh(fornitore)
        session.close()
        return(fornitore)

    @staticmethod
    def insert(JsonFornitore):
       session = Session()
       fornitore=Fornitore(JsonFornitore)
       session.add(fornitore)
       session.commit()
       session.refresh(fornitore)
       baselink="/v1/media/fornitore/"
       if fornitore.filepresentazione is not None:
        fornitore.filepresentazione=baselink+hashlib.md5(fornitore.email.encode('utf-8')).hexdigest()+'/'+fornitore.filepresentazione
       fornitore.querysearch=func.coalesce(fornitore.nome,"")+" "+func.coalesce(fornitore.cognome,"")+" "+func.coalesce(fornitore.email,"")+" "+func.coalesce(fornitore.azienda,"")
       session.add(fornitore)
       session.commit()
       session.refresh(fornitore)
       fid=fornitore.id
       session.close()
       return(fid)


    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        fornitore=session.query(Fornitore)
        totalCount=fornitore.count()

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(func.lower(getattr(Fornitore, key)).like("%{}%".format(value.lower())))
                elif key in ['provincia','tipologialocation','categoriafornitore']:
                    filters_tuple.append(func.lower(getattr(Fornitore, key)).in_((v.lower() for v in value)))  
                else:
                    filters_tuple.append(getattr(Fornitore, key) == value)
            fornitore=fornitore.filter(*filters_tuple)

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                fornitore=fornitore.order_by(Fornitore.__table__.columns[sorting[0]].asc())
            else:
                fornitore=fornitore.order_by(Fornitore.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            fornitore=fornitore.offset(pagination[0]).limit(pagination[1])

        fornitore=fornitore.all()
        session.close()
        return (fornitore,totalCount) 

    @staticmethod
    def updSupplier(supplier_id,fornitoreBase):
        session = Session()
        fornitore=session.query(Fornitore).filter(Fornitore.id==supplier_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = fornitoreBase.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(fornitore, key, value)
        baselink="/v1/media/fornitore/"
        fornitore.filepresentazione=baselink+hashlib.md5(fornitore.email.encode('utf-8')).hexdigest()+'/'+fornitore.filepresentazione
        fornitore.querysearch=func.coalesce(fornitore.nome,"")+" "+func.coalesce(fornitore.cognome,"")+" "+func.coalesce(fornitore.email,"")+" "+func.coalesce(fornitore.azienda,"")
        session.add(fornitore)
        session.commit()
        session.refresh(fornitore)
        session.close()
        return fornitore



    def __init__(self):
        pass
