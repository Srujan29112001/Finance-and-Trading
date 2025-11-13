"""Market Alerts API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()


class MarketAlert(BaseModel):
    id: int
    symbol: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool

    class Config:
        from_attributes = True


@router.get("/recent", response_model=List[MarketAlert])
async def get_recent_alerts(
    limit: int = 50,
    severity: str = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recent market alerts."""
    from app.models.alerts import MarketAlert as MarketAlertModel

    query = select(MarketAlertModel)
    if severity:
        query = query.where(MarketAlertModel.severity == severity.upper())
    query = query.order_by(MarketAlertModel.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()
    return [MarketAlert.from_orm(a) for a in alerts]


@router.get("/{symbol}", response_model=List[MarketAlert])
async def get_symbol_alerts(
    symbol: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session)
):
    """Get alerts for a specific symbol."""
    from app.models.alerts import MarketAlert as MarketAlertModel

    query = select(MarketAlertModel).where(
        MarketAlertModel.symbol == symbol.upper()
    ).order_by(MarketAlertModel.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    alerts = result.scalars().all()
    return [MarketAlert.from_orm(a) for a in alerts]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Acknowledge an alert."""
    from app.models.alerts import MarketAlert as MarketAlertModel

    query = select(MarketAlertModel).where(MarketAlertModel.id == alert_id)
    result = await db.execute(query)
    alert = result.scalar_one_or_none()

    if alert:
        alert.acknowledged = True
        await db.commit()
        return {"status": "acknowledged", "alert_id": alert_id}

    return {"error": "Alert not found"}
