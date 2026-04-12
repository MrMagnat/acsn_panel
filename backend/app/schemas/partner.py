from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PartnerStatsResponse(BaseModel):
    balance: int
    today_earned: int
    week_earned: int
    month_earned: int
    token_rate: int  # сколько токенов = $1


class PartnerTransactionResponse(BaseModel):
    id: str
    tool_name: Optional[str] = None
    amount: int
    description: str
    created_at: datetime
    model_config = {"from_attributes": True}


class PartnerToolResponse(BaseModel):
    id: str
    name: str
    description: str
    energy_cost: int
    model_config = {"from_attributes": True}


class WithdrawRequestCreate(BaseModel):
    amount: int
    comment: Optional[str] = None


class WithdrawRequestResponse(BaseModel):
    id: str
    amount: int
    comment: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    created_at: datetime
    user_id: str
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    model_config = {"from_attributes": True}
