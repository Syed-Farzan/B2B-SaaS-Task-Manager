from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_current_user, hash_password
from app.db.database import get_db
from app.models.users import Users
from app.schemas.user import TokenReturn, UserInvite, UserResponse

api_user = APIRouter()


@api_user.post("/users/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    data: UserInvite,
    db: AsyncSession = Depends(get_db),
    current_user: TokenReturn = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can invite users",
        )

    existing = await db.execute(select(Users).where(Users.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = Users(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        organization_id=current_user.organization_id,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
