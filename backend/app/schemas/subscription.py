from pydantic import BaseModel
from datetime import datetime


class TariffPlanPublic(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    price_usd: int = 0
    balance_usd_per_month: int = 0
    max_agents: int
    max_tools_per_agent: int
    max_workflows: int
    max_knowledge_bases: int = 1
    tokens_per_month: int
    is_default: bool = False
    sort_order: int = 0

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    id: str
    # Локальный тариф
    tariff_plan: TariffPlanPublic | None = None
    tokens_left: int = 0
    tokens_per_month: int = 0
    # ASCN-данные
    plan: str
    plan_name: str | None = None
    max_agents: int
    max_tools_per_agent: int
    energy_per_week: int
    energy_left: int
    balance_usd: int = 0
    renewed_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionWebhookUpdate(BaseModel):
    """Вебхук от системы подписок для обновления лимитов."""
    user_id: str
    plan: str
    max_agents: int
    max_tools_per_agent: int
    energy_per_week: int
