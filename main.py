from fastapi import FastAPI, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class ShiftUpdateRequest(BaseModel):
    comment: str = None
    start_time: datetime = None
    end_time: datetime = None

#engine = create_engine('sqlite:///database.db', echo=True)
SQLALCHEMY_DATABASE_URL = "postgresql://root:4f803929130dbfaeabd876b62ced6fab@db/db"
Base = declarative_base()

class Shift(Base):
    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    person = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    comment = Column(String)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)

class ShiftRequest(BaseModel):
    person: str

@app.get("/clock/{person}")
async def clock_in(person: str):
    # Get the last shift entry for the person
    last_shift = session.query(Shift).filter_by(person=person).order_by(Shift.id.desc()).first()

    if last_shift and not last_shift.end_time:
        # Update the end time to the current time
        last_shift.end_time = datetime.now()
        session.commit()
        return {"message": f"Shift ended for {person}"}

    # Create a new shift entry with start time
    new_shift = Shift(person=person, start_time=datetime.now())
    session.add(new_shift)
    session.commit()

    return {"message": f"Shift started for {person}"}

@app.get("/get/data/{person}")
async def get_data(person: str):
    shifts = session.query(Shift).filter_by(person=person).all()

    data = []
    for shift in shifts:
        data.append({
            "id": shift.id,
            "person": shift.person,
            "start_time": shift.start_time,
            "end_time": shift.end_time,
            "comment": shift.comment
        })

    return {"data": data}

@app.put("/shifts/{id}")
async def update_shift(id: int, shift_update: ShiftUpdateRequest):
    shift = session.query(Shift).get(id)

    if shift:
        if shift_update.comment is not None:
            shift.comment = shift_update.comment
        if shift_update.start_time is not None:
            shift.start_time = shift_update.start_time
        if shift_update.end_time is not None:
            shift.end_time = shift_update.end_time
        session.commit()
        return {"message": f"Shift with ID {id} updated."}
    else:
        return {"message": f"Shift with ID {id} not found."}

@app.get("/persons")
async def list_distinct_persons():
    distinct_persons = session.query(Shift.person).distinct().all()
    persons_list = [person[0] for person in distinct_persons]
    return {"distinct_persons": persons_list}

@app.get("/timecard")
async def generate_timecard(weekStartDate: str, person: str):
    # Calculate the start and end dates of the week
    start_date = datetime.strptime(weekStartDate, '%Y-%m-%d')
    print(start_date)
    end_date = start_date + timedelta(days=6)
    print(end_date)
    # Fetch the shifts for the specified week and person
    shifts = session.query(Shift).filter(
        Shift.person == person,
        Shift.start_time >= start_date,
        Shift.end_time <= end_date
    ).all()

    timecard_data = []
    for shift in shifts:
        total_hours = (shift.end_time - shift.start_time).total_seconds() / 3600
        amount = total_hours * 15  # Assuming $15 per hour rate

        timecard_data.append({
            "date": shift.start_time.date(),
            "shift": shift.comment,
            "start_time": shift.start_time.time(),
            "end_time": shift.end_time.time(),
            "total_hours": total_hours,
            "amount": amount
        })

    return timecard_data
