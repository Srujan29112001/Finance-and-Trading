"""Analysis and Sentiment API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db_session, get_mongodb
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

router = APIRouter()


class SentimentScore(BaseModel):
    symbol: str
    source: str
    sentiment_score: float
    sentiment_label: str
    timestamp: datetime

    class Config:
        from_attributes = True


class NewsArticle(BaseModel):
    title: str
    source: str
    url: Optional[str] = None
    published_at: datetime
    sentiment: Optional[float] = None
    summary: Optional[str] = None


@router.get("/sentiment/{symbol}", response_model=List[SentimentScore])
async def get_sentiment(
    symbol: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db_session)
):
    """Get sentiment scores for a symbol."""
    try:
        from app.models.sentiment import SentimentScore as SentimentScoreModel
        from sqlalchemy import select, and_

        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(SentimentScoreModel).where(
            and_(
                SentimentScoreModel.symbol == symbol.upper(),
                SentimentScoreModel.timestamp >= since
            )
        ).order_by(SentimentScoreModel.timestamp.desc())

        result = await db.execute(query)
        scores = result.scalars().all()

        return [SentimentScore.model_validate(s, from_attributes=True) for s in scores]

    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        return []


@router.get("/news/{symbol}", response_model=List[NewsArticle])
async def get_news(
    symbol: str,
    limit: int = 20
):
    """Get recent news articles for a symbol."""
    try:
        mongodb = get_mongodb()
        news_collection = mongodb["news_articles"]

        articles = news_collection.find(
            {"symbol": symbol.upper()}
        ).sort("published_at", -1).limit(limit)

        return [
            NewsArticle(
                title=article.get("title", ""),
                source=article.get("source", ""),
                url=article.get("url"),
                published_at=article.get("published_at", datetime.utcnow()),
                sentiment=article.get("sentiment"),
                summary=article.get("summary")
            )
            for article in articles
        ]

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []


@router.get("/sentiment/aggregate/{symbol}")
async def get_aggregate_sentiment(
    symbol: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db_session)
):
    """Get aggregated sentiment score."""
    try:
        from app.models.sentiment import SentimentScore as SentimentScoreModel
        from sqlalchemy import select, and_, func

        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(
            func.avg(SentimentScoreModel.sentiment_score).label("avg_sentiment"),
            func.count(SentimentScoreModel.id).label("count")
        ).where(
            and_(
                SentimentScoreModel.symbol == symbol.upper(),
                SentimentScoreModel.timestamp >= since
            )
        )

        result = await db.execute(query)
        row = result.first()

        avg_sentiment = float(row.avg_sentiment) if row.avg_sentiment else 0.0
        count = row.count if row.count else 0

        # Determine label
        if avg_sentiment > 0.1:
            label = "positive"
        elif avg_sentiment < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {
            "symbol": symbol,
            "avg_sentiment": avg_sentiment,
            "sentiment_label": label,
            "sample_size": count,
            "period_hours": hours
        }

    except Exception as e:
        logger.error(f"Error calculating aggregate sentiment: {e}")
        return {"error": str(e)}
