from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.subscription import Subscription
from ..models.tariff_plan import TariffPlan
from ..models.user import User
from ..schemas.subscription import SubscriptionResponse, TariffPlanPublic

router = APIRouter(prefix="/subscription", tags=["Подписка"])


@router.get("", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить текущую подписку пользователя."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .options(selectinload(Subscription.tariff_plan))
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        from datetime import datetime, timezone
        return SubscriptionResponse(
            id="",
            plan="free",
            max_agents=1,
            max_tools_per_agent=2,
            energy_per_week=100,
            energy_left=100,
            renewed_at=datetime.now(timezone.utc),
        )
    return subscription


@router.get("/plans", response_model=list[TariffPlanPublic])
async def list_tariff_plans(db: AsyncSession = Depends(get_db)):
    """Публичный список активных тарифных планов."""
    result = await db.execute(
        select(TariffPlan)
        .where(TariffPlan.is_active == True)
        .order_by(TariffPlan.sort_order, TariffPlan.created_at)
    )
    return result.scalars().all()
