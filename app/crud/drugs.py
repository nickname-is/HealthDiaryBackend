from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Drug
from core.schemas.drug import DrugBase, DrugUpdate


async def create_drug(session: AsyncSession, drug_create: DrugBase,) -> Drug:
    drug = Drug(**drug_create.model_dump())

    session.add(drug)
    await session.commit()
    await session.refresh(drug)

    return drug


async def update_drug(session: AsyncSession, drug: Drug,  drug_update: DrugUpdate, ) -> Drug:
    drug_data = drug_update.model_dump(exclude_unset=True)

    for field, value in drug_data.items():
        setattr(drug, field, value)

    session.add(drug)
    await session.commit()
    await session.refresh(drug)

    return drug
