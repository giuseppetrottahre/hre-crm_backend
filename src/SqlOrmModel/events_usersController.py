
from .base import Session, engine, Base
from .events_users import Event,User,EventsUsers
from sqlalchemy import asc, desc,text,and_,func,update, text
import json,uuid

class EventUserController:


    @staticmethod
    def checkProposalExistence(event_id,user_id):
        session = Session() 
        proposal=session.query(EventsUsers).filter(and_(EventsUsers.event_id==event_id,EventsUsers.user_id==user_id)).first()
        session.close()
        return proposal

    @staticmethod
    def confirmProposal(eventdata):
        proposal=EventUserController.checkProposalExistence(eventdata.event_id,eventdata.user_id)
        if proposal:
            proposal.status="Candidatura sottoposta"
        else:    
            proposal=EventsUsers(event_id=eventdata.event_id,user_id=eventdata.user_id,status="Candidatura sottoposta")
        session = Session() 
        session.add(proposal)
        session.commit() 
        session.refresh(proposal)
        session.close()
        return(proposal)        


    @staticmethod
    def manageCandidacy(operation,jsondata):
        session = Session()
        if operation.upper()=="ADD":
            session.execute(update(Event).where(Event.id==jsondata.event_id).values(users_id=text(f'array_append(users_id, :user_id)')),
        {'user_id': jsondata.user_id})

            session.execute(update(User).where(User.id==jsondata.user_id).values(events_id=text(f'array_append(events_id, :event_id)')),
        {'event_id': jsondata.event_id})
        else:  #DEL
            session.execute(update(Event).where(Event.id==jsondata.event_id).values(users_id=text(f'array_remove(users_id, :user_id)')),
        {'user_id': jsondata.user_id})

            session.execute(update(User).where(User.id==jsondata.user_id).values(events_id=text(f'array_remove(events_id, :event_id)')),
        {'event_id': jsondata.event_id})


        event=session.query(Event).filter(Event.id==jsondata.event_id).first()
        session.commit()
        session.refresh(event)
        session.close()
        return(event)  


    @staticmethod
    def checkCandidacy(event_id,user_id):
        session = Session() 
        exists=session.query(Event).filter(and_(Event.id==event_id,Event.users_id.contains([user_id]))).first()
        session.commit()
        session.close()
        if exists:
            return True
        else:
            return False

    @staticmethod
    def insert(eventBase):
        session = Session()
        event=Event(eventBase)
        session.add(event)
        session.commit()
        session.refresh(event)
        if event.urlcandidature:
            event.linkcandidaturaweb=event.urlcandidature+"/?ide="+str(event.id)   
            event.linkcandidaturautenti=event.urlcandidature+"/?ide="+str(event.id)+"&ida=[idanagrafica]"
        event.querysearch=func.coalesce(event.nomeevento,"")+" "+func.coalesce(event.descrizione,"")
        session.add(event)
        session.commit()
        session.refresh(event)
        session.close()
        return(event)

    @staticmethod
    def getEvent(event_id):
        session = Session()
        event=session.query(Event).filter(Event.id==event_id).first()
        session.refresh(event)
        session.close()
        return(event)

    @staticmethod
    def checkEventid(event_id):
        session = Session()
        exists=session.query(Event).filter(Event.id==event_id).first()
        session.close()
        if exists:
            return True
        else:
            return False


    @staticmethod
    def delEvent(event_id):
        session = Session()
        event=session.query(Event).filter(Event.id==event_id).first()
        users=session.query(User).filter(User.events_id.any(event_id)).all()
        for user in users:
            user.events_id.remove(event_id)
            session.add(user)
        session.delete(event)
        session.commit()
        session.close()
        return(event)       

    @staticmethod
    def proposeEventUser(jsondata):
        session = Session()
        proposal=EventsUsers(event_id=jsondata.event_id,user_id=jsondata.user_id,status="Notifica inviata")
        session.add(proposal)
        session.commit()
        event=session.query(Event).filter(Event.id==proposal.event_id).first()
        user=session.query(User).filter(User.id==proposal.user_id).first()
        email=user.mail
        message="Notifica evanto:\n"+str(event.id)+"-"+event.nomeevento+"\n\n"+event.descrizione+"\n\n"
        message+="Per candidarsi all'evento cliccare sul seguente link:"+event.linkcandidaturautenti.replace("[idanagrafica]",str(user.id))
        session.close()
        return (message,email)

    @staticmethod
    def getFreeUsersList(filters,range,sort):
        session = Session()
        users_ids=session.query(EventsUsers.user_id).filter(EventsUsers.event_id==filters["event_id"])
        users=session.query(User).filter(User.id.not_in(users_ids))
        del filters["event_id"]
        if bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(getattr(User, key).like("%{}%".format(value)))
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
    def getEngagedUsersList(filters,range,sort):
        session = Session()
        users=session.query(User,EventsUsers.status).join(EventsUsers,User.id==EventsUsers.user_id).filter(EventsUsers.event_id==filters["event_id"])
        del filters["event_id"]
        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column
        #of postgresql
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(getattr(User, key).like("%{}%".format(value)))
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
        proposals=[]
        for user,status in users:
            user.status=status
            proposals.append(user)

        session.close()
        return (proposals,totalCount)

    @staticmethod
    def getUserProposals(filters,range,sort):
        session = Session()
        events_ids=session.query(EventsUsers.event_id).filter(EventsUsers.user_id==filters["user_id"])
        events=session.query(Event).filter(Event.id.in_(events_ids))
        del filters["user_id"]
        if bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(getattr(Event, key).like("%{}%".format(value)))
                else:
                    filters_tuple.append(getattr(Event, key) == value)
            events=events.filter(*filters_tuple)
        totalCount=events.count()
        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                events=events.order_by(Event.__table__.columns[sorting[0]].asc())
            else:
                events=events.order_by(Event.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            events=events.offset(pagination[0]).limit(pagination[1])
 
        events=events.all()
        session.close()
        return (events,totalCount)



    @staticmethod
    def getUsersList(filters,range,sort):
        (objlis,objcount)=([],0)
        if bool(filters):
            if "get_events" in filters:
                get_events=filters["get_events"]
                del filters["get_events"]
                if get_events:
                    (objlis,objcount)= EventUserController.getUserProposals(filters,range,sort)
            elif "events_id_negate" in filters:
                events_id_negate=filters["events_id_negate"]
                del filters["events_id_negate"]
                if events_id_negate :
                    (objlis,objcount)= EventUserController.getFreeUsersList(filters,range,sort)
                else:
                    (objlis,objcount)= EventUserController.getEngagedUsersList(filters,range,sort)
            
        return (objlis,objcount)

    @staticmethod
    def updEvent(event_id,eventBase):
        session = Session()
        event=session.query(Event).filter(Event.id==event_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = eventBase.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        event.linkcandidaturaweb=event.urlcandidature+"/?ide="+str(event.id)   
        event.linkcandidaturautenti=event.urlcandidature+"/?ide="+str(event.id)+"&ida=[idanagrafica]"
        event.querysearch=func.coalesce(event.nomeevento,"")+" "+func.coalesce(event.descrizione,"")
        session.add(event)
        session.commit()
        session.refresh(event)
        session.close()
        return event

    def __init__(self):
        pass