from collections.abc import Sequence

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.base import Base


class CRUDBase[
    ModelType: Base,
    CreateSchemaType: BaseModel,
    UpdateSchemaType: BaseModel,
]:
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> ModelType | None:
        return await session.get(self.model, id)

    async def get_multi(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        result = await session.scalars(
            select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        )

        return result.all()

    async def create(
        self, session: AsyncSession, obj_in: CreateSchemaType, commit: bool = True
    ) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)

        if commit:
            await session.commit()
            await session.refresh(db_obj)
        else:
            await session.flush()

        return db_obj

    async def update(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        commit: bool = True,
    ) -> ModelType:
        if not isinstance(db_obj, self.model):
            raise TypeError(
                f"db_obj must be of type {self.model.__name__}, "
                f"but got {type(db_obj).__name__}"
            )

        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        session.add(db_obj)

        if commit:
            await session.commit()
            await session.refresh(db_obj)
        else:
            await session.flush()

        return db_obj

    async def delete(
        self,
        session: AsyncSession,
        db_obj: ModelType,
        commit: bool = True,
    ) -> ModelType:
        if not isinstance(db_obj, self.model):
            raise TypeError(
                f"db_obj must be of type {self.model.__name__}, "
                f"but got {type(db_obj).__name__}"
            )

        await session.delete(db_obj)

        if commit:
            await session.commit()
        else:
            await session.flush()

        return db_obj
