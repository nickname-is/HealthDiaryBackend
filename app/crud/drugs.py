from app.core.models import Drug
from app.core.schemas.drug import DrugBase, DrugUpdate
from app.crud.base import CRUDBase


class CRUDDrug(CRUDBase[Drug, DrugBase, DrugUpdate]):
    pass


drugs_crud = CRUDDrug(Drug)
