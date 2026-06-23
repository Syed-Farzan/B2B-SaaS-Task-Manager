from app.db.database import Base
import uuid
from sqlalchemy import Column, String, DateTime, UUID
import datetime


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
