from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta

from ..core.db import get_db
from ..core.deps import get_current_user
from ..models.user import User
from ..models.tool import Tool
from ..models.subscription import Subscription
from ..models.partner_transaction import PartnerTransaction, WithdrawRequest
from ..models.setting import Setting
from ..schemas.partner import PartnerStatsResponse, PartnerTransactionResponse, PartnerToolResponse, WithdrawRequestCreate, WithdrawRequestResponse

router = APIRouter(prefix="/partner", tags=["partner"])

DEFAULT_RATE = 1000  # 1000 токенов = $1


async def _get_partner_rate(db: AsyncSession) -> int:
    result = await db.execute(select(Setting).where(Setting.key == "partner_token_rate"))
    row = result.scalar_one_or_none()
    if row:
        try:
            return int(row.value)
        except Exception:
            pass
    return DEFAULT_RATE


@router.get("/me", response_model=PartnerStatsResponse)
async def get_partner_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = sub_result.scalar_one_or_none()
    balance = sub.partner_tokens if sub else 0

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    async def _sum_earned(since: datetime) -> int:
        res = await db.execute(
            select(func.coalesce(func.sum(PartnerTransaction.amount), 0))
            .where(PartnerTransaction.user_id == current_user.id,
                   PartnerTransaction.amount > 0,
                   PartnerTransaction.created_at >= since)
        )
        return res.scalar() or 0

    rate = await _get_partner_rate(db)
    return PartnerStatsResponse(
        balance=balance,
        today_earned=await _sum_earned(today_start),
        week_earned=await _sum_earned(week_start),
        month_earned=await _sum_earned(month_start),
        token_rate=rate,
    )


@router.get("/tools", response_model=list[PartnerToolResponse])
async def get_partner_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Tool).where(Tool.owner_user_id == current_user.id, Tool.is_active == True)
    )
    return result.scalars().all()


@router.get("/transactions", response_model=list[PartnerTransactionResponse])
async def get_partner_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PartnerTransaction)
        .where(PartnerTransaction.user_id == current_user.id)
        .order_by(PartnerTransaction.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


@router.post("/withdraw", response_model=WithdrawRequestResponse, status_code=201)
async def request_withdraw(
    data: WithdrawRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = sub_result.scalar_one_or_none()
    if not sub or sub.partner_tokens < data.amount:
        raise HTTPException(status_code=400, detail="Недостаточно партнёрских токенов")
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть положительной")

    req = WithdrawRequest(
        user_id=current_user.id,
        amount=data.amount,
        comment=data.comment,
        status="pending",
    )
    db.add(req)
    await db.flush()

    result = WithdrawRequestResponse(
        id=req.id,
        amount=req.amount,
        comment=req.comment,
        status=req.status,
        admin_note=req.admin_note,
        created_at=req.created_at,
        user_id=req.user_id,
    )
    return result
