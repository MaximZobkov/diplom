from flask_login import UserMixin
from . import SqlAlchemyBase
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    email_confirmed = Column(Boolean, nullable=False, default=False)
    confirmed_on = Column(DateTime, nullable=True)
