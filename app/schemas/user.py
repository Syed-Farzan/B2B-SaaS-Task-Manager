from pydantic import BaseModel, EmailStr


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
    organization_id: str
