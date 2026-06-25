from fastapi import APIRouter, Depends, HTTPException
from app.schemas.project import ProjectCreate, ProjectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.projects import Projects
from app.schemas.user import TokenReturn
from sqlalchemy.future import select

api_proj = APIRouter()


@api_proj.post("/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenReturn = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create projects",
        )
    project_data = Projects(
        title=project.title,
        description=project.description,
        organization_id=current_user.organization_id,
    )
    db.add(project_data)
    await db.commit()
    await db.refresh(project_data)
    return project_data


@api_proj.get("/projects", response_model=list[ProjectResponse])
async def get_project(
    db: AsyncSession = Depends(get_db),
    current_user: TokenReturn = Depends(get_current_user),
):
    data_b = await db.execute(
        select(Projects).where(Projects.organization_id == current_user.organization_id)
    )
    project = data_b.scalars().all()
    return project
