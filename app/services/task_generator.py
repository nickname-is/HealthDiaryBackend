from typing import Optional
from datetime import timezone, datetime
from dateutil.relativedelta import relativedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.models import db_helper
from core.models.task_repeat import RepeatTypeEnum, TaskRepeat
from core.models.task import Task
from core.models.drug import Drug
from crud import tasks as crud_tasks


async def generate_task(session: AsyncSession, base_task: Task) -> Optional[Task]:
    repeat_task = base_task.repeat

    if not repeat_task:
        return None

    if repeat_task.repeat_type == RepeatTypeEnum.DAY:
        delta = relativedelta(days=repeat_task.repeat_interval)
    elif repeat_task.repeat_type == RepeatTypeEnum.WEEK:
        delta = relativedelta(weeks=repeat_task.repeat_interval)
    elif repeat_task.repeat_type == RepeatTypeEnum.MONTH:
        delta = relativedelta(months=repeat_task.repeat_interval)
    elif repeat_task.repeat_type == RepeatTypeEnum.YEAR:
        delta = relativedelta(years=repeat_task.repeat_interval)
    else:
        return None

    new_start_datetime = base_task.start_datetime + delta
    new_end_datetime = base_task.end_datetime + delta

    is_reminded = new_start_datetime < datetime.now(timezone.utc)
    new_task = Task(
        guid=uuid.uuid4(),
        user_id=base_task.user_id,
        title=base_task.title,
        all_day=base_task.all_day,
        start_datetime=new_start_datetime,
        end_datetime=new_end_datetime,
        reminder_minutes=base_task.reminder_minutes,
        is_completed=False,
        is_reminded=is_reminded,
    )

    if base_task.drug:
        new_drug = Drug(
            name=base_task.drug.name,
            dosage=base_task.drug.dosage,
            dosage_unit=base_task.drug.dosage_unit,
            dosage_type=base_task.drug.dosage_type,
            task=new_task  # связываем через relationship
        )
        session.add(new_drug)

    new_repeat = TaskRepeat(
        repeat_type=repeat_task.repeat_type,
        repeat_interval=repeat_task.repeat_interval,
        task=new_task  # связываем через relationship
    )
    session.add(new_repeat)
    await session.delete(repeat_task)

    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    return await crud_tasks.get_task(session=session, task_guid=new_task.guid, user_id=base_task.user_id)


async def generate_repeated_tasks():
    async with db_helper.session_factory() as session:
        # Выбираем все задачи, у которых есть повторение и срок начала <= текущего времени
        result = await session.execute(
            select(Task)
            .join(TaskRepeat)
            .options(selectinload(Task.drug), selectinload(Task.repeat))
            .where(Task.start_datetime <= datetime.now(timezone.utc))
        )
        tasks = result.scalars().all()

        for task in tasks:
            await generate_task(session=session, base_task=task)
