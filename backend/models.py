from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    specialty = Column(String(100))
    hospital = Column(String(255))
    location = Column(String(255))


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer)
    interaction_date = Column(DateTime, default=datetime.utcnow)
    channel = Column(String(50))
    products_discussed = Column(String(255))
    summary = Column(Text)
    sentiment = Column(String(20))
    follow_up_action = Column(Text)
    raw_input = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)