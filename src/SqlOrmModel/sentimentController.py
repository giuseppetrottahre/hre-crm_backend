
from .base import Session, engine, Base
from .events_users import User
from .comune import Comune
from .user_sentiment_detection import UserSentiment
from sqlalchemy import asc, desc,func,not_,or_,text,and_,update, text,extract
import uuid

class SentimentController:


    @staticmethod
    def insert(sentiment_row):
        session=Session()
        session.add(sentiment_row)
        session.commit()
        session.refresh(sentiment_row)
        sid=sentiment_row.id
        session.close()
        return(sid)




    @staticmethod
    def getList(filters,range,sort):
        session = Session()
        userssentiment=session.query(UserSentiment)
        

        #Filtering
        #filters are exact match apart q operator that use a like over text field collapsed in a special column 
        #of postgresql 
        if  bool(filters):
            filters_tuple = []
            for key, value in filters.items():  # type: str, any
                filters_tuple.append(getattr(UserSentiment, key).like("%{}%".format(value)))
            userssentiment=userssentiment.filter(*filters_tuple)
        totalCount=userssentiment.count()

        #Sorting
        #sort is a string array for example sort=["name","ASC|DESC"]
        if sort:
            sorting=sort.replace("[","").replace("]","").replace("\"","").split(",")
            if sorting[1].upper()=="ASC":
                userssentiment=userssentiment.order_by(UserSentiment.__table__.columns[sorting[0]].asc())
            else:
                userssentiment=userssentiment.order_by(UserSentiment.__table__.columns[sorting[0]].desc())

        #Pagination
        #calculate offset and limit starting from range as string range=[n1,n2] so remove [] split for "," 
        # and cast to int thw two numbers
        if range:
            offset,r_end=map(int,range.replace("[","").replace("]","").split(","))
            pagination=(offset,r_end-offset+1)  #offset=pagenumber r_end-offset=number of record
            userssentiment=userssentiment.offset(pagination[0]).limit(pagination[1])

        userssentiment=userssentiment.all()
        session.close()
        return (userssentiment,totalCount)

    @staticmethod
    def getSingleRow(sentiment_id):
        session = Session()
        usersentiment=session.query(UserSentiment).filter(UserSentiment.id==sentiment_id).first()
        session.refresh(usersentiment)
        session.close()
        return(usersentiment)



    @staticmethod
    def updateSingleRow(sentiment_id,sentimentData):
        session = Session()
        usersentiment=session.query(UserSentiment).filter(UserSentiment.id==sentiment_id).first()
        #if not event:
        #    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        update_data = sentimentData.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(usersentiment, key, value)
        session.add(usersentiment)
        session.commit()
        session.refresh(usersentiment)
        session.close()
        return usersentiment 


    @staticmethod
    def remove_sentiment(sentiment_id):
        session = Session()
        session.query(UserSentiment).filter(UserSentiment.id==sentiment_id).delete()
        session.commit()
        session.close()
        return(True)

    
    def __init__(self):
        pass
