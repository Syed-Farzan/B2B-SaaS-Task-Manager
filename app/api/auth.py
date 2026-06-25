from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.orgnization import Organization
from app.models.users import Users
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.schemas.user import UserRegister, TokenReturn, UserLogin

api = APIRouter()


@api.post("/register", status_code=201)
async def register_user(data: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Users).where(Users.email == data.email))

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    org = Organization(name=data.organization_name)
    db.add(org)
    await db.flush()
    org_id = org.id

    hashed_pass = hash_password(password=data.password)
    usr = Users(
        email=data.email,
        hashed_password=hashed_pass,
        role="Admin",
        organization_id=org_id,
    )
    db.add(usr)
    await db.commit()
    await db.refresh(usr)
    return {"user_id": usr.id, "organization": org.name, "role": usr.role}


from fastapi.security import OAuth2PasswordRequestForm


@api.post("/login", status_code=200)
async def login(
    data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Users).where(Users.email == data.username))
    email_exists = result.scalar_one_or_none()

    if not email_exists or not verify_password(
        data.password, email_exists.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {
            "sub": str(email_exists.email),
            "role": email_exists.role,
            "organization_id": str(email_exists.organization_id),
        }
    )
    return {"access_token": token, "token_type": "bearer"}


@api.get("/me", response_model=TokenReturn)
async def test_gatekeeper(current_user: TokenReturn = Depends(get_current_user)):
    return current_user
