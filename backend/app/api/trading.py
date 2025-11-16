"""Trading Signals and RL Agent API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import pandas as pd

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


class BacktestRequest(BaseModel):
    """Backtest request parameters"""
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 100000.0
    strategy_name: str = "RL Agent Strategy"


class BacktestResponse(BaseModel):
    """Backtest results"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    volatility: float
    var_95: float
    cvar_95: float
    equity_curve: List[float]
    daily_returns: List[float]


@router.post("/backtest", response_model=BacktestResponse)
async def backtest_strategy(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Run a comprehensive backtest of the trading strategy.

    This endpoint simulates trading using the RL agent's signals on historical data
    and provides detailed performance metrics including:
    - Total and annualized returns
    - Risk-adjusted metrics (Sharpe, Sortino ratios)
    - Drawdown analysis
    - Win/loss statistics
    - Value at Risk (VaR)
    """
    try:
        from app.services.backtesting import BacktestEngine, Action
        from app.models.market import StockPrice

        # Set default dates if not provided
        end_date = request.end_date or datetime.utcnow()
        start_date = request.start_date or (end_date - timedelta(days=30))

        logger.info(f"Running backtest for {request.symbol} from {start_date} to {end_date}")

        # Fetch historical price data
        from sqlalchemy import select
        query = select(StockPrice).where(
            StockPrice.symbol == request.symbol.upper(),
            StockPrice.timestamp >= start_date,
            StockPrice.timestamp <= end_date
        ).order_by(StockPrice.timestamp)

        result = await db.execute(query)
        prices = result.scalars().all()

        if len(prices) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient historical data for {request.symbol}. Need at least 10 data points."
            )

        # Convert to DataFrame
        price_data = pd.DataFrame([
            {
                'timestamp': p.timestamp,
                'symbol': p.symbol,
                'price': float(p.close),
                'volume': p.volume
            }
            for p in prices
        ])

        # Generate signals using RL agent
        # For demo purposes, we'll create sample signals
        # In production, this would use the actual RL agent to generate signals
        from app.agents.rl_agent import get_rl_agent

        agent = get_rl_agent()
        signals_list = []

        for i, row in price_data.iterrows():
            # Generate signal for each data point
            try:
                signal = await agent.generate_signal(
                    request.symbol,
                    current_price=row['price']
                )

                signals_list.append({
                    'timestamp': row['timestamp'],
                    'symbol': request.symbol,
                    'action': signal.get('signal_type', 'HOLD'),
                    'quantity': 100  # Fixed quantity for simplicity
                })
            except Exception as e:
                logger.warning(f"Error generating signal at {row['timestamp']}: {e}")
                signals_list.append({
                    'timestamp': row['timestamp'],
                    'symbol': request.symbol,
                    'action': 'HOLD',
                    'quantity': 0
                })

        signals_df = pd.DataFrame(signals_list)

        # Run backtest
        engine = BacktestEngine(initial_capital=request.initial_capital)
        result = engine.run_backtest(
            signals=signals_df,
            price_data=price_data,
            strategy_name=request.strategy_name
        )

        # Return results
        return BacktestResponse(
            strategy_name=result.strategy_name,
            symbol=request.symbol,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_capital=result.final_capital,
            total_return=result.total_return,
            total_return_pct=result.total_return_pct,
            annualized_return=result.annualized_return,
            sharpe_ratio=result.sharpe_ratio,
            sortino_ratio=result.sortino_ratio,
            max_drawdown=result.max_drawdown,
            max_drawdown_pct=result.max_drawdown_pct,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            win_rate=result.win_rate,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
            profit_factor=result.profit_factor,
            volatility=result.volatility,
            var_95=result.var_95,
            cvar_95=result.cvar_95,
            equity_curve=result.equity_curve,
            daily_returns=result.daily_returns
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/backtest/quick/{symbol}")
async def quick_backtest(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to backtest"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Quick backtest endpoint (GET) for simpler access.

    Run a 30-day backtest with default parameters.
    """
    request = BacktestRequest(
        symbol=symbol,
        end_date=datetime.utcnow(),
        start_date=datetime.utcnow() - timedelta(days=days),
        initial_capital=100000.0,
        strategy_name=f"RL Agent - {symbol} ({days}d)"
    )

    return await backtest_strategy(request, db)
