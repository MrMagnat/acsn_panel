from pydantic import BaseModel
from datetime import datetime


class SubscriptionResponse(BaseModel):
    id: str
    plan: str
    plan_name: str | None = None
    max_agents: int
    max_tools_per_agent: int
    energy_per_week: int
    energy_left: int
    balance_usd: int = 0  # в центах
    renewed_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionWebhookUpdate(BaseModel):
    """Вебхук от системы подписок для обновления лимитов."""
    user_id: str
    plan: str
    max_agents: int
    max_tools_per_agent: int
    energy_per_week: int
