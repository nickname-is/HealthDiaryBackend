from fastapi import APIRouter

from core.config import settings

from .users import router as users_router
from .auth import router as auth_router
from .tasks import router as tasks_router
from .activities import router as activities_router
from .water_intakes import router as water_intakes_router
from .sleeps import router as sleeps_router

router = APIRouter(
    prefix=settings.api.v1.prefix,
)
router.include_router(
    users_router,
    prefix=settings.api.v1.users,
)
router.include_router(
    auth_router,
    prefix=settings.api.v1.auth,
)
router.include_router(
    tasks_router,
    prefix=settings.api.v1.tasks,
)
router.include_router(
    activities_router,
    prefix=settings.api.v1.activities,
)
router.include_router(
    water_intakes_router,
    prefix=settings.api.v1.water_intakes,
)
router.include_router(
    sleeps_router,
    prefix=settings.api.v1.sleeps,
)