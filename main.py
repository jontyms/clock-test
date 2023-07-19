from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from fastapi.staticfiles import StaticFiles


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class ShiftUpdateRequest(BaseModel):
    comment: str = None
    start_time: datetime = None
    end_time: datetime = None

engine = create_engine('sqlite:///database.db', echo=True)

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

# Route handler
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