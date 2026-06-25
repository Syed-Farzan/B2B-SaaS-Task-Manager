from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class TaskCreate(BaseModel):

    title: str
    status: str = "To Do"
    priority: str = "Medium"


class TaskResponse(BaseModel):

    id: UUID
    title: str
    status: str
    priority: str
    project_id: UUID
    assignee_id: UUID | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskStatus(BaseModel):
    status: str


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
