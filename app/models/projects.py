from sqlalchemy import Column, String, UUID, DateTime, Integer, ForeignKey, Text
import uuid
import datetime
from app.db.database import Base


class Projects(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
