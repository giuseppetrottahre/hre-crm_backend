
from .base import Session, engine, Base
from .events_users import User
from .comune import Comune
from .user_sentiment_detection import UserSentiment
from .user_timesheet_detection import UserTimesheet
from sqlalchemy import asc, desc,func,not_,or_,text,and_,update, text,extract
import uuid

class TimesheetController:


    @staticmethod
    def insert(timesheet_row):
        session=Session()
        session.add(timesheet_row)
        session.commit()
        session.refresh(timesheet_row)
        uid=timesheet_row.id
        session.close()
        return(uid)


    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        userstimesheet=session.query(UserTimesheet)
        

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                filters_tuple.append(getattr(UserTimesheet, key).like("%{}%".format(value)))
            userstimesheet=userstimesheet.filter(*filters_tuple)
        totalCount=userstimesheet.count()

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                userstimesheet=userstimesheet.order_by(UserTimesheet.__table__.columns[sorting[0]].asc())
            else:
                userstimesheet=userstimesheet.order_by(UserTimesheet.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            userstimesheet=userstimesheet.offset(pagination[0]).limit(pagination[1])

        userstimesheet=userstimesheet.all()
        session.close()
        return (userstimesheet,totalCount)

    @staticmethod
    def getSingleRow(timesheet_id):
        session = Session()
        usertimesheet=session.query(UserTimesheet).filter(UserTimesheet.id==timesheet_id).first()
        session.refresh(usertimesheet)
        session.close()
        return(usertimesheet)

    @staticmethod
    def closeTimeSheet(timesheet_id):
        session = Session()
        timesheet_row=session.query(UserTimesheet).filter(UserTimesheet.id==timesheet_id).first()
        timesheet_row.stoptimestamp=func.now()
        session.add(timesheet_row)
        session.commit()
        session.refresh(timesheet_row)
        session.close()
        return timesheet_row 

    @staticmethod
    def updateSingleRow(timesheet_id,timesheetData):
        session = Session()
        usertimesheet=session.query(UserTimesheet).filter(UserTimesheet.id==timesheet_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = timesheetData.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(usertimesheet, key, value)
        session.add(usertimesheet)
        session.commit()
        session.refresh(usertimesheet)
        session.close()
        return usertimesheet 


    @staticmethod
    def remove_timesheet(timesheet_id):
        session = Session()
        session.query(UserTimesheet).filter(UserTimesheet.id==timesheet_id).delete()
        session.commit()
        session.close()
        return(True)


    @staticmethod
    def getSingleRowOpenForUserId(user_id):
        timesheet_id=None
        session = Session()
        timesheet_row=session.query(UserTimesheet).filter(UserTimesheet.id_user==str(user_id),UserTimesheet.stoptimestamp==None).first()
        if timesheet_row:
            timesheet_id=timesheet_row.id
        session.commit()
        session.close()
        return (timesheet_id)

    
    def __init__(self):
        pass
