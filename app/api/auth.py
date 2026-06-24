from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.models.orgnization import Organization
from app.models.users import Users
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserRegister, UserLogin

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


@api.post("/login", status_code=200)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):

    email = await db.execute(select(Users).where(Users.email == data.email))
    email_exists = email.scalar_one_or_none()

    if not email_exists:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, email_exists.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {
            "sub": email_exists.id,
            "role": email_exists.role,
            "organization_id": email_exists.organization_id,
        }
    )
    return token
