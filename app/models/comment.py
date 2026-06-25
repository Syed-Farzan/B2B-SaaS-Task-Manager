from app.db.database import Base
import uuid
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
import datetime


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="Cascade"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
