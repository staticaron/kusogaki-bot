from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from kusogaki_bot.data.db import Base


class FoodCounter(Base):
    __tablename__ = 'food_counters'

    user_id = Column(String, primary_key=True)
    count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())


class Reminder(Base):
    __tablename__ = 'reminders'

    user_id = Column(String, primary_key=True)
    data = Column(JSON, default={})


class ScheduledThread(Base):
    __tablename__ = 'scheduled_threads'

    id = Column(Integer, primary_key=True)
    data = Column(JSON, default={})
