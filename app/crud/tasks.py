from datetime import datetime, time
from typing import Optional, Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fastapi import HTTPException
from starlette import status

from core.models import Task, Drug, TaskRepeat
from core.schemas.task import TaskCreate, TaskUpdate


async def create_task(session: AsyncSession, user_id: int, task_in: TaskCreate) -> Task:
    if task_in.guid:
        existing_task = await session.scalar(
            select(Task).where(Task.guid == task_in.guid)
        )
        if existing_task:
            task_in.guid = uuid.uuid4()

    task_data = task_in.model_dump(exclude={"drug", "repeat"})
    task_data["user_id"] = user_id
    task_data["guid"] = task_in.guid or uuid.uuid4()
    if task_in.all_day:
        task_data["start_datetime"] = datetime.combine(
            task_in.start_datetime.date(), time.min
        )
        task_data["end_datetime"] = datetime.combine(
            task_in.end_datetime.date(), time.max
        )

    if (
        task_data["start_datetime"]
        and task_data["end_datetime"]
        and task_data["end_datetime"] < task_data["start_datetime"]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The end date must be after the start date.",
        )

    task = Task(**task_data)

    if task_in.drug:
        task.drug = Drug(**task_in.drug.model_dump())

    if task_in.repeat:
        task.repeat = TaskRepeat(**task_in.repeat.model_dump())

    session.add(task)
    await session.commit()
    await session.refresh(task)

    stmt = (
        select(Task)
        .where(Task.id == task.id)
        .options(selectinload(Task.drug), selectinload(Task.repeat))
    )
    task = await session.scalar(stmt)

    return task


async def get_task(
    session: AsyncSession, task_guid: uuid.UUID, user_id: int
) -> Optional[Task]:
    statement = (
        select(Task)
        .where(Task.guid == task_guid, Task.user_id == user_id)
        .options(selectinload(Task.drug), selectinload(Task.repeat))
    )
    return await session.scalar(statement)


async def get_tasks(session: AsyncSession, user_id: int) -> Sequence[Task]:
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.start_datetime)
        .options(selectinload(Task.drug), selectinload(Task.repeat))
    )
    result = await session.scalars(statement)
    return result.all()


async def update_task(
    session: AsyncSession, task: Task, task_update: TaskUpdate
) -> Task:
    update_data = task_update.model_dump(exclude_unset=True)
    simple_fields = {
        k: v for k, v in update_data.items() if k not in ("drug", "repeat")
    }

    for field, value in simple_fields.items():
        if field in update_data:
            setattr(task, field, update_data[field])

    if "all_day" in simple_fields and simple_fields["all_day"]:
        task.start_datetime = datetime.combine(task.start_datetime.date(), time.min)
        task.end_datetime = datetime.combine(task.end_datetime.date(), time.max)

    if (
        task.start_datetime
        and task.end_datetime
        and task.end_datetime < task.start_datetime
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The end date must be after the start date.",
        )

    if "drug" in update_data:
        drug_data = update_data["drug"]
        if drug_data:
            if task.drug:
                for key, value in drug_data.items():
                    setattr(task.drug, key, value)
            else:
                task.drug = Drug(**drug_data)
        else:
            if task.drug:
                await session.delete(task.drug)

    if "repeat" in update_data:
        repeat_data = update_data["repeat"]
        if repeat_data:
            if task.repeat:
                for key, value in repeat_data.items():
                    setattr(task.repeat, key, value)
            else:
                task.repeat = TaskRepeat(**repeat_data)
        else:
            if task.repeat:
                await session.delete(task.repeat)

    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()
