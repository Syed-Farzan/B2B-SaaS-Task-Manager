from sqlalchemy import Column, String, UUID, DateTime, Integer, ForeignKey, Text
import uuid
import datetime
from app.db.database import Base


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="To Do")
    priority = Column(String(50), default="Medium")
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
