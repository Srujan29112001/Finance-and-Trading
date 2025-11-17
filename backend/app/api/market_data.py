"""
Market Data API Endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db_session, get_redis
import json

router = APIRouter()


# Pydantic models
class StockPrice(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None

    class Config:
        from_attributes = True


class TechnicalIndicator(BaseModel):
    symbol: str
    date: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None

    class Config:
        from_attributes = True


class MarketSummary(BaseModel):
    symbol: str
    current_price: float
    change: float
    change_pct: float
    volume: int
    high_24h: float
    low_24h: float
    timestamp: datetime


@router.get("/prices/{symbol}", response_model=List[StockPrice])
async def get_stock_prices(
    symbol: str,
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    interval: str = Query(default="1m", description="1m, 5m, 1h, 1d"),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get historical price data for a symbol.

    - **symbol**: Stock ticker symbol (e.g., AAPL, TSLA)
    - **start**: Start datetime (default: 24 hours ago)
    - **end**: End datetime (default: now)
    - **interval**: Time interval for bars
    - **limit**: Maximum number of records to return
    """
    try:
        # Default time range
        if not end:
            end = datetime.utcnow()
        if not start:
            start = end - timedelta(days=1)

        # Check cache first
        cache_key = f"prices:{symbol}:{start.isoformat()}:{end.isoformat()}:{limit}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {symbol} prices")
            return json.loads(cached)

        # Query from database
        from app.models.market import StockPrice as StockPriceModel
        query = select(StockPriceModel).where(
            and_(
                StockPriceModel.symbol == symbol.upper(),
                StockPriceModel.timestamp >= start,
                StockPriceModel.timestamp <= end
            )
        ).order_by(StockPriceModel.timestamp.desc()).limit(limit)

        result = await db.execute(query)
        prices = result.scalars().all()

        response = [StockPrice.model_validate(p, from_attributes=True) for p in prices]

        # Cache the result
        await redis.setex(cache_key, 60, json.dumps([p.model_dump() for p in response], default=str))

        return response

    except Exception as e:
        logger.error(f"Error fetching prices for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/{symbol}", response_model=StockPrice)
async def get_latest_price(
    symbol: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get the latest price for a symbol."""
    try:
        # Check cache
        cache_key = f"latest_price:{symbol}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Query from materialized view
        from app.models.market import LatestStockPrice
        query = select(LatestStockPrice).where(LatestStockPrice.symbol == symbol.upper())
        result = await db.execute(query)
        price = result.scalar_one_or_none()

        if not price:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        response = StockPrice.model_validate(price, from_attributes=True)

        # Cache for 5 seconds
        await redis.setex(cache_key, 5, json.dumps(response.model_dump(), default=str))

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{symbol}", response_model=MarketSummary)
async def get_market_summary(
    symbol: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get market summary for a symbol (current price, 24h change, etc.)."""
    try:
        from app.models.market import StockPrice as StockPriceModel

        # Get latest price
        latest_query = select(StockPriceModel).where(
            StockPriceModel.symbol == symbol.upper()
        ).order_by(StockPriceModel.timestamp.desc()).limit(1)
        latest_result = await db.execute(latest_query)
        latest = latest_result.scalar_one_or_none()

        if not latest:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Get 24h ago price
        day_ago = datetime.utcnow() - timedelta(days=1)
        day_ago_query = select(StockPriceModel).where(
            and_(
                StockPriceModel.symbol == symbol.upper(),
                StockPriceModel.timestamp >= day_ago
            )
        ).order_by(StockPriceModel.timestamp.asc()).limit(1)
        day_ago_result = await db.execute(day_ago_query)
        day_ago_price = day_ago_result.scalar_one_or_none()

        # Calculate change
        if day_ago_price:
            change = latest.close - day_ago_price.close
            change_pct = (change / day_ago_price.close) * 100
        else:
            change = 0
            change_pct = 0

        # Get 24h high/low
        stats_query = select(StockPriceModel).where(
            and_(
                StockPriceModel.symbol == symbol.upper(),
                StockPriceModel.timestamp >= day_ago
            )
        )
        stats_result = await db.execute(stats_query)
        stats = stats_result.scalars().all()

        high_24h = max([s.high for s in stats]) if stats else latest.high
        low_24h = min([s.low for s in stats]) if stats else latest.low
        total_volume = sum([s.volume for s in stats]) if stats else latest.volume

        return MarketSummary(
            symbol=symbol.upper(),
            current_price=latest.close,
            change=change,
            change_pct=change_pct,
            volume=total_volume,
            high_24h=high_24h,
            low_24h=low_24h,
            timestamp=latest.timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators/{symbol}", response_model=List[TechnicalIndicator])
async def get_technical_indicators(
    symbol: str,
    start: Optional[datetime] = Query(default=None),
    limit: int = Query(default=30, le=365),
    db: AsyncSession = Depends(get_db_session)
):
    """Get technical indicators for a symbol."""
    try:
        if not start:
            start = datetime.utcnow() - timedelta(days=30)

        from app.models.market import TechnicalIndicator as TechnicalIndicatorModel
        query = select(TechnicalIndicatorModel).where(
            and_(
                TechnicalIndicatorModel.symbol == symbol.upper(),
                TechnicalIndicatorModel.date >= start.date()
            )
        ).order_by(TechnicalIndicatorModel.date.desc()).limit(limit)

        result = await db.execute(query)
        indicators = result.scalars().all()

        return [TechnicalIndicator.model_validate(ind, from_attributes=True) for ind in indicators]

    except Exception as e:
        logger.error(f"Error fetching indicators for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_available_symbols(db: AsyncSession = Depends(get_db_session)):
    """Get list of available symbols in the system."""
    try:
        from app.models.market import StockPrice as StockPriceModel
        query = select(StockPriceModel.symbol).distinct()
        result = await db.execute(query)
        symbols = [row[0] for row in result.all()]

        return {"symbols": symbols, "count": len(symbols)}

    except Exception as e:
        logger.error(f"Error fetching available symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))
