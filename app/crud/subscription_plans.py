from app.core.models.subscription_plan import SubscriptionPlan
from app.core.schemas.subscription_plan import SubscriptionPlanRead
from app.crud.base import CRUDBase


class CRUDSubscriptionPlan(
    CRUDBase[SubscriptionPlan, SubscriptionPlanRead, SubscriptionPlanRead]
):
    pass


subscription_plans_crud = CRUDSubscriptionPlan(SubscriptionPlan)
