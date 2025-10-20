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

from api.deps import get_current_user

from core.models import db_helper
from core.models.user import User
from core.schemas.task import TaskRead, TaskCreate, TaskUpdate

import crud.tasks as crud_tasks


log = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks"])


@router.get("/", response_model=list[TaskRead])
async def read_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    tasks = await crud_tasks.get_tasks(session=session, user_id=current_user.id)
    return tasks


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.create_task(session=session, user_id=current_user.id, task_in=task_in)
    return task


@router.put("/{task_guid}", response_model=TaskRead)
async def update_existing_task(
    task_guid: uuid.UUID,
    task_update: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.get_task(session, task_guid=task_guid, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updated_task = await crud_tasks.update_task(session, task, task_update)
    return updated_task


@router.delete("/{task_guid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_task(
    task_guid: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    task = await crud_tasks.get_task(session, task_guid=task_guid, user_id=current_user.id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await crud_tasks.delete_task(session, task)
    return
