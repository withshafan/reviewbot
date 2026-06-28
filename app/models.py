from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, index=True)
    repo = Column(String, index=True)
    pr_number = Column(Integer, index=True)
    head_sha = Column(String)
    total_issues = Column(Integer)
    decision = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
