import uvicorn

from core.config import settings

from api import router as api_router
from media_router import router as media_router

from create_fastapi_app import create_app

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

from slowapi.errors import RateLimitExceeded

main_app = create_app(
    create_custom_static_urls=True,
)
main_app.include_router(
    api_router,
)
main_app.include_router(
    media_router,
)


@main_app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "There are too many requests. Try again later."},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
