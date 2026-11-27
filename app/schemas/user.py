from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    organization_name: str


class UserInvite(BaseModel):
    email: EmailStr
    password: str
    role: Literal["Admin", "Member"] = "Member"


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    organization_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenReturn(BaseModel):
    user: EmailStr
    role: str
    organization_id: UUID
