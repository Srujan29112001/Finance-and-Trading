"""Portfolio Management API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class PortfolioPosition(BaseModel):
    symbol: str
    quantity: float
    avg_purchase_price: float
    current_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None

    class Config:
        from_attributes = True


class RiskMetrics(BaseModel):
    portfolio_value: float
    var_95: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("/{user_id}/positions", response_model=List[PortfolioPosition])
async def get_portfolio_positions(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get user's portfolio positions."""
    from app.models.portfolio import UserPortfolio
    from sqlalchemy import select

    query = select(UserPortfolio).where(UserPortfolio.user_id == user_id)
    result = await db.execute(query)
    positions = result.scalars().all()
    return [PortfolioPosition.model_validate(p, from_attributes=True) for p in positions]


@router.get("/{user_id}/risk", response_model=RiskMetrics)
async def get_risk_metrics(
    user_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get portfolio risk metrics."""
    from app.models.portfolio import RiskMetrics as RiskMetricsModel
    from sqlalchemy import select

    query = select(RiskMetricsModel).where(
        RiskMetricsModel.user_id == user_id
    ).order_by(RiskMetricsModel.timestamp.desc()).limit(1)

    result = await db.execute(query)
    metrics = result.scalar_one_or_none()

    if metrics:
        return RiskMetrics.model_validate(metrics, from_attributes=True)

    return RiskMetrics(portfolio_value=0.0)
