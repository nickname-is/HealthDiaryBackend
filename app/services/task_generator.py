import uuid
from datetime import UTC, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import db_helper
from app.core.models.drug import Drug
from app.core.models.task import Task
from app.core.models.task_repeat import RepeatTypeEnum, TaskRepeat
from app.crud.tasks import tasks_crud

TASKS_BATCH_SIZE = 100


async def generate_task(session: AsyncSession, base_task: Task) -> Task | None:
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

    is_reminded = new_start_datetime < datetime.now(UTC)
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
            task=new_task,  # связываем через relationship
        )
        session.add(new_drug)

    new_repeat = TaskRepeat(
        repeat_type=repeat_task.repeat_type,
        repeat_interval=repeat_task.repeat_interval,
        task=new_task,  # связываем через relationship
    )
    session.add(new_repeat)
    await session.delete(repeat_task)

    session.add(new_task)
    await session.flush()
    await session.refresh(new_task)

    return await tasks_crud.get_task(
        session=session, task_guid=new_task.guid, user_id=base_task.user_id
    )


async def generate_repeated_tasks() -> None:
    async with db_helper.session_factory() as session:
        while True:
            result = await session.execute(
                select(Task)
                .join(TaskRepeat)
                .options(selectinload(Task.drug), selectinload(Task.repeat))
                .where(Task.start_datetime <= datetime.now(UTC))
                .limit(TASKS_BATCH_SIZE)
            )
            tasks = result.scalars().all()

            if not tasks:
                break

            for task in tasks:
                await generate_task(session=session, base_task=task)

            await session.commit()
