import logging
import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.deps import check_user_permission
from app.core.models import db_helper
from app.core.models.task import Task
from app.core.models.user import User
from app.core.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.crud.tasks import tasks_crud

log = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.get("", response_model=list[TaskRead])
async def read_tasks(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Sequence[Task]:
    tasks = await tasks_crud.get_tasks(session=session, user_id=user_id)
    return tasks


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    user_id: int,
    task_in: TaskCreate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Task:
    task = await tasks_crud.create_task(
        session=session, user_id=user_id, task_in=task_in
    )
    return task


@router.patch("/{task_guid}", response_model=TaskRead)
async def update_task(
    user_id: int,
    task_guid: uuid.UUID,
    task_update: TaskUpdate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Task:
    task = await tasks_crud.get_task(session, task_guid=task_guid, user_id=user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    updated_task = await tasks_crud.update_task(session, task, task_update)
    return updated_task


@router.delete("/{task_guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    user_id: int,
    task_guid: uuid.UUID,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> None:
    task = await tasks_crud.get_task(session, task_guid=task_guid, user_id=user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    await tasks_crud.delete(session, task)
    return
