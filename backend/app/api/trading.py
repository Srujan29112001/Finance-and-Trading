"""Trading Signals and RL Agent API"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

router = APIRouter()


class TradingSignal(BaseModel):
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    confidence: float
    price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/signals/{symbol}", response_model=List[TradingSignal])
async def get_trading_signals(
    symbol: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
):
    """Get recent trading signals from RL agent."""
    try:
        from app.models.trading import TradingSignal as TradingSignalModel
        from sqlalchemy import select

        query = select(TradingSignalModel).where(
            TradingSignalModel.symbol == symbol.upper()
        ).order_by(TradingSignalModel.timestamp.desc()).limit(limit)

        result = await db.execute(query)
        signals = result.scalars().all()

        return [TradingSignal.from_orm(s) for s in signals]

    except Exception as e:
        logger.error(f"Error fetching trading signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/generate")
async def generate_trading_signal(
    symbol: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a new trading signal using RL agent."""
    try:
        from app.agents.rl_agent import get_rl_agent

        agent = get_rl_agent()
        signal = await agent.generate_signal(symbol)

        # Save to database
        from app.models.trading import TradingSignal as TradingSignalModel
        db_signal = TradingSignalModel(**signal)
        db.add(db_signal)
        await db.commit()

        return signal

    except Exception as e:
        logger.error(f"Error generating trading signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/{symbol}")
async def backtest_strategy(symbol: str, days: int = 30):
    """Backtest RL trading strategy."""
    return {
        "symbol": symbol,
        "period": f"{days} days",
        "status": "Backtesting functionality - to be implemented",
        "note": "This would run historical simulation of the RL agent's performance"
    }
