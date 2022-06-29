from .backendUserSession import BackendUserSession
from .base import Session
from .backendUser import BackendUser
from sqlalchemy import Column, String,Integer,DateTime,func,text
import datetime
import hashlib 

class BackendController:

    @staticmethod
    def resetPwd(username,pwdtmp):
        session = Session()
        user_email=None
        user=session.query(BackendUser).filter(BackendUser.username==username).first()
        if user is not None:
            user.password=hashlib.md5(pwdtmp.encode('utf-8')).hexdigest()
            user.firstlogin=True
            session.add(user)
            session.commit()
            session.refresh(user)
            user_email=user.email
        session.close()
        return(user_email)        


    @staticmethod
    def insert(accountBase):
        session = Session()
        account=BackendUser(accountBase)
        account.firstlogin=True
        session.add(account)
        session.commit()
        session.refresh(account)
        session.close()
        return(account)

    @staticmethod
    def delAccount(account_id):
        session = Session()
        session.query(BackendUserSession).filter(BackendUserSession.user_id==str(account_id)).delete()
        session.query(BackendUser).filter(BackendUser.id==account_id).delete()
        session.commit()
        session.close()
        return(True)




    @staticmethod
    def updAccount(account_id,accountBase):
        session = Session()
        account=session.query(BackendUser).filter(BackendUser.id==account_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = accountBase.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(account, key, value)
        session.add(account)
        session.commit()
        session.refresh(account)
        session.close()
        return account




    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        session = Session()
        accounts=session.query(BackendUser)
        

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(func.lower(getattr(BackendUser, key)).like("%{}%".format(value.lower())))
                else:
                    filters_tuple.append(getattr(BackendUser, key) == value)
            accounts=accounts.filter(*filters_tuple)
        totalCount=accounts.count()

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                accounts=accounts.order_by(BackendUser.__table__.columns[sorting[0]].asc())
            else:
                accounts=accounts.order_by(BackendUser.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            accounts=accounts.offset(pagination[0]).limit(pagination[1])

        accounts=accounts.all()
        session.close()
        return (accounts,totalCount)
    

    @staticmethod
    def login(JsonBackendUser):
        session_id,user_id,user_permissions,user_firstLogin=None,None,None,None
        session = Session()
        user_bck=BackendUser(JsonBackendUser)
        user=session.query(BackendUser).filter(BackendUser.username==user_bck.username,BackendUser.password==user_bck.password).first()
        if user:
                session.query(BackendUserSession).filter(BackendUserSession.user_id==str(user.id)).delete()
                user_session_bck=BackendUserSession(user_id=str(user.id))
                session.add(user_session_bck)
                session.flush()
                session.commit()
                session.refresh(user_session_bck)
                session_id=user_session_bck.session_id
                user_id=user_session_bck.user_id
                user_permissions=user.permissions
                user_firstLogin=user.firstlogin
        session.close()
        return (session_id,user_id,user_permissions,user_firstLogin)


    @staticmethod
    def changePwd(JsonBackendUser):
        session = Session()
        status=False
        user_newpwd=BackendUser(JsonBackendUser)
        user=session.query(BackendUser).filter(BackendUser.username==user_newpwd.username).first()
        if user:
                user.password=user_newpwd.password
                user.firstlogin=False
                session.add(user)
                session.commit()
                session.refresh(user)
                status=True
        session.close()
        return (status)


    @staticmethod
    def checkSession(session_id):
        session = Session()
        isvalid=False
        SESSION_ID_VALIDITY_SECONDS = 8*60*60  #number of seconds of validity session_id from lastupdatetime
        oldtimestamp=datetime.datetime.today() - datetime.timedelta(seconds=SESSION_ID_VALIDITY_SECONDS)
        session.query(BackendUserSession).filter(BackendUserSession.lastupdatetimestmp <= oldtimestamp).delete()
        session.commit()
        userSession=session.query(BackendUserSession).filter(BackendUserSession.session_id==session_id).first()
        if userSession:
            userSession.callcount=userSession.callcount+1
            session.add(userSession)
            session.commit()
            session.refresh(userSession)
            isvalid=True
        session.close()
        return isvalid

    @staticmethod
    def getAccount(account_id):
        session = Session()
        account=session.query(BackendUser).filter(BackendUser.id == account_id).first()
        session.close()
        return account

    @staticmethod
    def checkAccount(username):
        session = Session()
        account=session.query(BackendUser).filter(BackendUser.username == username).first()
        session.close()
        return (account != None)


    @staticmethod
    def logout(JsonBackendUserSessionID):
        session = Session()
        session.query(BackendUserSession).filter(BackendUserSession.session_id==JsonBackendUserSessionID).delete()
        session.commit()
        session.close()



    def __init__(self):
        pass