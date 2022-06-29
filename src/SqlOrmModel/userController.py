
from .base import Session, engine, Base
from .events_users import Event,User
from .comune import Comune
from .user_delete_request import UserDeleteRequest
from.events_users import EventsUsers
from sqlalchemy import asc, desc,func,not_,or_,text,and_,update, text,extract
import uuid

class UserController:

    @staticmethod
    def insert(JsonUser):
        session = Session()
        user=User(JsonUser)
        user.querysearch=func.coalesce(user.nome,"")+" "+func.coalesce(user.secondonome,"")+" "+func.coalesce(user.cognome,"")+" "+func.coalesce(user.note,"")+" "+func.coalesce(user.codicefiscale)+" "+func.coalesce(user.mail)
        baselink="/v1/media/utente/"
        user.codicefiscale=user.codicefiscale.upper()
        user.filenameinputcv=baselink+user.codicefiscale+'/'+user.filenameinputcv
        user.filenameinputprofiloimg=baselink+user.codicefiscale+'/'+user.filenameinputprofiloimg
       # uid=None; #if exists remains to None otherwise will be set in the next code block  
       # exists = session.query(User).filter(User.codicefiscale==user.codicefiscale).first()
       # if exists is None:
            #get region
        comune=session.query(Comune).filter(Comune.provincia==user.provincia).first()
        user.regione=comune.regione
            #persists data
        session.add(user)
        session.commit()
        session.refresh(user)
        uid=user.id
        session.close()
        return(uid)


    @staticmethod
    def checkCf(codiceFiscale):
        session = Session()
        exists = session.query(User).filter(func.lower(User.codicefiscale)==codiceFiscale.lower()).first()
        userid=False
        if exists:
            userid=exists.id
        session.close()
        return userid

    @staticmethod
    def getEmail(codiceFiscale):
        session = Session()
        exists = session.query(User).filter(func.lower(User.codicefiscale)==codiceFiscale.lower()).first()
        userEmail=False
        if exists:
            userEmail=exists.mail
        session.close()
        return userEmail

    @staticmethod
    def getCf(user_id):
        session = Session()
        user = session.query(User).filter(User.id==user_id).first()
        codicefiscale=user.codicefiscale
        session.commit()
        session.close()
        return codicefiscale

    @staticmethod
    def checkUserid(userid):
        session = Session()
        exists = session.query(User).filter(User.id==userid).first()
        #commit and close session
        session.commit()
        session.close()
        if exists:
            return True
        else:
            return False



    #ritorna l'id della richiesta di cancellazione se lo user esiste altrimenti False
    @staticmethod
    def  delete_request(codiceFiscale):
        session = Session()
        id_delete_request=None
        user = session.query(User).filter(func.lower(User.codicefiscale)==codiceFiscale.lower()).first()
        if user is not None:
            ud_req=UserDeleteRequest(str(user.id))
            session.add(ud_req)
            session.commit()
            session.refresh(ud_req)         
            id_delete_request=ud_req.id
        session.close()
        return id_delete_request
          

    #rimuove l'utente che ha una richiesta di cancellazione confermata dal link inviato via email.
    @staticmethod
    def remove(user_delete_request_id):
        userid=None
        session = Session()
        ud_req=session.query(UserDeleteRequest).filter(UserDeleteRequest.id==user_delete_request_id).first()
        userCf=None
        if ud_req is not None:
            userid=ud_req.id_user
            user=session.query(User).filter(User.id==userid).first()
            if user:
                userCf=user.codicefiscale
                UserController.delUser(userid)
            session.query(UserDeleteRequest).filter(UserDeleteRequest.id==user_delete_request_id).delete()
        session.commit()
        session.close()
        return userCf

    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        users=session.query(User)
        

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            if "events_id_negate" in filters:
                events_id_negate=filters["events_id_negate"]
                del filters["events_id_negate"]
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(func.lower(getattr(User, key)).like("%{}%".format(value.lower())))
                elif key=='minage':
                    filters_tuple.append(extract('year', func.age(User.datadinascita)) >= value)
                elif key=='maxage':
                    filters_tuple.append(extract('year', func.age(User.datadinascita)) < value)    
                elif key in ['regione', 'provincia', 'citta', 'inglese','francese','tedesca','spagnola','coloreocchi','colorecapelli','stato', 'valutazione']:
                    filters_tuple.append(func.lower(getattr(User, key)).in_((v.lower() for v in value)))  
                elif key in ['altezza', 'numeroscarpe','tagliavestito']:
                    filters_tuple.append(func.lower(getattr(User, key))==str(value))           
                elif key=='events_id':
                    if events_id_negate:
                        filters_tuple.append(or_(not_(getattr(User, key).any(value)),getattr(User, key)==None))
                    else:    
                        filters_tuple.append(getattr(User, key).any(value))
                else:
                    filters_tuple.append(getattr(User, key) == value)
            users=users.filter(*filters_tuple)
        totalCount=users.count()

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                users=users.order_by(User.__table__.columns[sorting[0]].asc())
            else:
                users=users.order_by(User.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            users=users.offset(pagination[0]).limit(pagination[1])

        users=users.all()
        session.close()
        return (users,totalCount)

    @staticmethod
    def getUser(user_id):
        session = Session()
        user=session.query(User).filter(User.id==user_id).first()
        session.refresh(user)
        session.close()
        return(user)

    @staticmethod
    def updUser(user_id,userBase):
        session = Session()
        user=session.query(User).filter(User.id==user_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = userBase.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        user.querysearch=func.coalesce(user.nome,"")+" "+func.coalesce(user.secondonome,"")+" "+func.coalesce(user.cognome,"")+" "+func.coalesce(user.note,"")+" "+func.coalesce(user.codicefiscale)+" "+func.coalesce(user.mail)
        user.codicefiscale=user.codicefiscale.upper()
        baselink="/v1/media/utente/"+user.codicefiscale
        if not user.filenameinputcv.startswith(baselink):
            user.filenameinputcv=baselink+'/'+user.filenameinputcv
        if not user.filenameinputprofiloimg.startswith(baselink):
            user.filenameinputprofiloimg=baselink+'/'+user.filenameinputprofiloimg
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()
        return user

    @staticmethod
    def delUser(user_id):
        session = Session()
        session.query(EventsUsers).filter(EventsUsers.user_id==user_id).delete()
        session.query(User).filter(User.id==user_id).delete()
        session.commit()
        session.close()
        return(True)   


    def __init__(self):
        pass
