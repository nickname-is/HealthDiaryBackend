from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from starlette import status

from app.core.models import User
from app.core.schemas.user import UserCreate, UserUpdate
from app.core.security import get_hash_password, verify_password
from app.crud.base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    @staticmethod
    async def check_unique(
        session: AsyncSession,
        column: InstrumentedAttribute,
        value: str | EmailStr,
        user_id: int | None = None,
    ) -> None:
        existing = await session.scalar(select(User).where(column == value))

        if existing and (user_id is None or existing.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with this {column.key} already exists.",
            )

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        user: User | None = await session.scalar(
            select(User).where(User.email == email)
        )

        return user

    async def create(
        self,
        session: AsyncSession,
        obj_in: UserCreate,
        commit: bool = True,
    ) -> User:
        await self.check_unique(session, User.email, obj_in.email)

        obj_in.password = get_hash_password(obj_in.password)

        return await super().create(
            session=session,
            obj_in=obj_in,
            commit=commit,
        )

    async def update(
        self,
        session: AsyncSession,
        db_obj: User,
        obj_in: UserUpdate,
        commit: bool = True,
    ) -> User:
        if obj_in.password is not None:
            obj_in.password = get_hash_password(obj_in.password)

        return await super().update(
            session=session,
            db_obj=db_obj,
            obj_in=obj_in,
            commit=commit,
        )

    async def verify_user(
        self, session: AsyncSession, user_id: int, commit: bool = True
    ) -> User | None:
        db_user = await self.get(session=session, id=user_id)
        if db_user is None:
            return None

        db_user.is_verified = True
        session.add(db_user)

        if commit:
            await session.commit()
            await session.refresh(db_user)
        else:
            await session.flush()

        return db_user

    async def authenticate(
        self, session: AsyncSession, email: str, password: str
    ) -> User | None:
        db_user = await self.get_by_email(session=session, email=email)
        if not db_user:
            return None
        if not verify_password(password, db_user.password):
            return None

        return db_user


users_crud = CRUDUser(User)
