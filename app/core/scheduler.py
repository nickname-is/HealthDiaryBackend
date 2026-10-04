from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.task_generator import generate_repeated_tasks

scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    scheduler.add_job(generate_repeated_tasks, CronTrigger(minute="*"))
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
