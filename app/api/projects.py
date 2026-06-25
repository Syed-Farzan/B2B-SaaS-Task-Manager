from fastapi import APIRouter, Depends, HTTPException
from app.schemas.project import ProjectCreate, ProjectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.projects import Projects
from app.schemas.user import TokenReturn
from sqlalchemy.future import select
from app.schemas.tasks import TaskCreate, TaskResponse, TaskStatus
from app.models.tasks import Tasks
from uuid import UUID

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


@api_proj.post("/projects/{project_id}/tasks", response_model=TaskResponse)
async def create_task(
    project_id: UUID,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenReturn = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create tasks",
        )
    project_act = await db.execute(select(Projects).where(Projects.id == project_id))

    project = project_act.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    if project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )
    task_pack = Tasks(
        title=task.title,
        status=task.status,
        priority=task.priority,
        project_id=project.id,
    )
    db.add(task_pack)
    await db.commit()
    await db.refresh(task_pack)
    return task_pack


@api_proj.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    task: TaskStatus,
    db: AsyncSession = Depends(get_db),
    current_user: TokenReturn = Depends(get_current_user),
):
    task_result = await db.execute(select(Tasks).where(Tasks.id == task_id))
    task_db = task_result.scalar_one_or_none()

    if task_db is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    project_result = await db.execute(
        select(Projects).where(Projects.id == task_db.project_id)
    )
    project = project_result.scalar_one_or_none()

    if project is None or project.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task_db.status = task.status

    await db.commit()
    await db.refresh(task_db)

    return task_db
