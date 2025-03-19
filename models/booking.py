from . import SqlAlchemyBase
from sqlalchemy import Column, Integer, String, Date, Time

class Booking(SqlAlchemyBase):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    service = Column(String(100), nullable=False)
