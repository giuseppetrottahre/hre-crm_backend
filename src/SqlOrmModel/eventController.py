
from .base import Session, engine, Base
from .events_users import Event,User
from sqlalchemy import asc, desc,text,and_,func,update, text
import json,uuid
from.events_users import EventsUsers


class EventController:



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
        event.descrizione=func.coalesce(event.descrizione,"")
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
        session.query(EventsUsers).filter(EventsUsers.event_id==event_id).delete()
        event=session.query(Event).filter(Event.id==event_id).delete()
        session.commit()
        session.close()
        return(True)       

    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        events=session.query(Event)
        totalCount=events.count()

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                if key=='querysearch':
                    filters_tuple.append(getattr(Event, key).like("%{}%".format(value)))
                elif key=='users_id':
                    filters_tuple.append(getattr(Event, key).any(value))      
                else:
                    filters_tuple.append(getattr(Event, key) == value)
            events=events.filter(*filters_tuple)

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
    def updEvent(event_id,eventBase):
        session = Session()
        event=session.query(Event).filter(Event.id==event_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = eventBase.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        if event.urlcandidature:
            event.linkcandidaturaweb=event.urlcandidature+"/?ide="+event_id  
            event.linkcandidaturautenti=event.urlcandidature+"/?ide="+event_id+"&ida=[idanagrafica]"
        event.querysearch=func.coalesce(event.nomeevento,"")+" "+func.coalesce(event.descrizione,"")
        event.descrizione=func.coalesce(event.descrizione,"")
        session.add(event)
        session.commit()
        session.refresh(event)
        session.close()
        return event

    def __init__(self):
        pass