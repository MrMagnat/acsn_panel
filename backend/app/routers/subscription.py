from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.subscription import Subscription
from ..models.user import User
from ..schemas.subscription import SubscriptionResponse

router = APIRouter(prefix="/subscription", tags=["Подписка"])


@router.get("", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить текущую подписку пользователя."""
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        from ..models.base import gen_uuid
        from datetime import datetime, timezone
        # Дефолтная подписка если не существует
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
