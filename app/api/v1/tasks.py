import logging
import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import check_user_permission

from core.models import db_helper
from core.models.user import User
from core.schemas.task import TaskRead, TaskCreate, TaskUpdate

import crud.tasks as crud_tasks


log = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.get("/", response_model=list[TaskRead])
async def read_tasks(
    user_id: int,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    tasks = await crud_tasks.get_tasks(session=session, user_id=user_id)
    return tasks


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    user_id: int,
    task_in: TaskCreate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.create_task(session=session, user_id=user_id, task_in=task_in)
    return task


@router.put("/{task_guid}", response_model=TaskRead)
async def update_existing_task(
    user_id: int,
    task_guid: uuid.UUID,
    task_update: TaskUpdate,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.get_task(session, task_guid=task_guid, user_id=user_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updated_task = await crud_tasks.update_task(session, task, task_update)
    return updated_task


@router.delete("/{task_guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    user_id: int,
    task_guid: uuid.UUID,
    _current_user: Annotated[User, Depends(check_user_permission)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.get_task(session, task_guid=task_guid, user_id=user_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await crud_tasks.delete_task(session, task)
    return
