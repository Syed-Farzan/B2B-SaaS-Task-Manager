from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
