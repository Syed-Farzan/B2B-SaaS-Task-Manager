from pydantic import BaseModel, EmailStr

from uuid import UUID


class UserRegister(BaseModel):

    email: EmailStr
    password: str
    organization_name: str


class UserLogin(BaseModel):

    email: EmailStr
    password: str


class TokenReturn(BaseModel):

    user: EmailStr
    role: str
    organization_id: UUID
