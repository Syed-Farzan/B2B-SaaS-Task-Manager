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


@api_task.post("/tasks/{task_id}/comments", response_model=CommentResponse)
async def create_comment(
    task_id: UUID,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenReturn = Depends(get_current_user),
):

    task = await db.execute(select(Tasks).where(Tasks.id == task_id))
    task = task.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    project = await db.execute(select(Projects).where(Projects.id == task.project_id))

    project = project.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )
    if not project.organization_id == user.organization_id:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    email = await db.execute(select(Users).where(Users.email == user.user))

    email = email.scalar_one_or_none()

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    comments = Comment(task_id=task.id, user_id=email.id, content=comment.content)
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

    comments = await db.execute(select(Comment).where(Comment.task_id == task_id))
    return comments.scalars().all()
