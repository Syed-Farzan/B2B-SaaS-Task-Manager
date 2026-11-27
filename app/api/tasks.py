from fastapi import APIRouter, Depends, HTTPException
from app.schemas.tasks import CommentCreate, CommentResponse
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.core.security import get_current_user
from app.schemas.user import TokenReturn
from app.models.tasks import Tasks
from app.models.projects import Projects
from app.models.comment import Comment
from app.models.users import Users

api_task = APIRouter()


async def _get_tenant_task(
    task_id: UUID, organization_id: UUID, db: AsyncSession
) -> Tasks:
    task_result = await db.execute(select(Tasks).where(Tasks.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_result = await db.execute(
        select(Projects).where(Projects.id == task.project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project or project.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@api_task.post("/tasks/{task_id}/comments", response_model=CommentResponse)
async def create_comment(
    task_id: UUID,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenReturn = Depends(get_current_user),
):
    task = await _get_tenant_task(task_id, user.organization_id, db)

    user_result = await db.execute(select(Users).where(Users.email == user.user))
    db_user = user_result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    comments = Comment(task_id=task.id, user_id=db_user.id, content=comment.content)
    db.add(comments)
    await db.commit()
    await db.refresh(comments)
    return comments


@api_task.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
async def get_comments_for_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenReturn = Depends(get_current_user),
):
    await _get_tenant_task(task_id, user.organization_id, db)
    comments = await db.execute(select(Comment).where(Comment.task_id == task_id))
    return comments.scalars().all()
