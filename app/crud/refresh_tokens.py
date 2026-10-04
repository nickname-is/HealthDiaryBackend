from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import RefreshToken
from app.core.schemas.token import RefreshTokenCreate
from app.crud.base import CRUDBase


class CRUDRefreshToken(CRUDBase[RefreshToken, RefreshTokenCreate, RefreshTokenCreate]):
    @staticmethod
    async def get_by_token(session: AsyncSession, token: str) -> RefreshToken | None:
        result = await session.scalar(
            select(RefreshToken).where(RefreshToken.token == token)
        )

        return result

    @staticmethod
    async def get_by_user(
        session: AsyncSession, user_id: int
    ) -> Sequence[RefreshToken]:
        result = await session.scalars(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )

        return result.all()

    @staticmethod
    async def delete_all_by_user(session: AsyncSession, user_id: int) -> None:
        await session.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )

        await session.commit()


refresh_tokens_crud = CRUDRefreshToken(RefreshToken)
