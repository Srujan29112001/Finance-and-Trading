"""
GraphQL API implementation using Strawberry

This module provides a unified GraphQL interface for querying market data,
news, sentiment, and AI analysis results in a single request.
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from strawberry.fastapi import GraphQLRouter
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.market import StockPrice, TechnicalIndicator
from app.models.trading import TradingSignal
from app.models.sentiment import NewsArticle, SentimentScore
from app.models.alerts import MarketAlert


# GraphQL Types
@strawberry.type
class PriceHistory:
    """Stock price data point"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    @strawberry.field
    def change_percent(self) -> float:
        """Calculate price change percentage"""
        if self.open > 0:
            return ((self.close - self.open) / self.open) * 100
        return 0.0


@strawberry.type
class TechnicalIndicators:
    """Technical indicator values"""
    symbol: str
    date: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None


@strawberry.type
class News:
    """News article"""
    headline: str
    content: str
    source: str
    timestamp: datetime
    sentiment: float
    url: Optional[str] = None


@strawberry.type
class Sentiment:
    """Aggregated sentiment score"""
    symbol: str
    score: float
    label: str
    timestamp: datetime
    news_count: int
    social_count: int


@strawberry.type
class TradingSignalType:
    """Trading signal from RL agent"""
    symbol: str
    action: str
    confidence: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    timestamp: datetime
    reasoning: Optional[str]


@strawberry.type
class Alert:
    """Market alert"""
    alert_type: str
    symbol: str
    message: str
    severity: str
    timestamp: datetime
    price_at_alert: Optional[float]


@strawberry.type
class MarketSummary:
    """Complete market summary for a symbol"""
    symbol: str
    latest_price: Optional[PriceHistory]
    indicators: Optional[TechnicalIndicators]
    sentiment: Optional[Sentiment]
    latest_signal: Optional[TradingSignalType]
    recent_alerts: List[Alert]
    recent_news: List[News]


@strawberry.type
class AnalysisResult:
    """AI analysis result"""
    answer: str
    confidence: float
    sources: List[str]
    timestamp: datetime


# GraphQL Queries
@strawberry.type
class Query:
    """GraphQL query root"""

    @strawberry.field
    async def price_history(
        self,
        symbol: str,
        limit: int = 100,
        info: strawberry.Info = None
    ) -> List[PriceHistory]:
        """Get historical price data for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(desc(StockPrice.timestamp))
            .limit(limit)
        )
        result = await db.execute(stmt)
        prices = result.scalars().all()

        return [
            PriceHistory(
                timestamp=p.timestamp,
                open=float(p.open),
                high=float(p.high),
                low=float(p.low),
                close=float(p.close),
                volume=p.volume
            )
            for p in prices
        ]

    @strawberry.field
    async def latest_price(
        self,
        symbol: str,
        info: strawberry.Info = None
    ) -> Optional[PriceHistory]:
        """Get the latest price for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(desc(StockPrice.timestamp))
            .limit(1)
        )
        result = await db.execute(stmt)
        price = result.scalar_one_or_none()

        if not price:
            return None

        return PriceHistory(
            timestamp=price.timestamp,
            open=float(price.open),
            high=float(price.high),
            low=float(price.low),
            close=float(price.close),
            volume=price.volume
        )

    @strawberry.field
    async def technical_indicators(
        self,
        symbol: str,
        info: strawberry.Info = None
    ) -> Optional[TechnicalIndicators]:
        """Get latest technical indicators for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(TechnicalIndicator)
            .where(TechnicalIndicator.symbol == symbol)
            .order_by(desc(TechnicalIndicator.date))
            .limit(1)
        )
        result = await db.execute(stmt)
        indicator = result.scalar_one_or_none()

        if not indicator:
            return None

        return TechnicalIndicators(
            symbol=indicator.symbol,
            date=indicator.date,
            sma_20=float(indicator.sma_20) if indicator.sma_20 else None,
            sma_50=float(indicator.sma_50) if indicator.sma_50 else None,
            sma_200=float(indicator.sma_200) if indicator.sma_200 else None,
            rsi_14=float(indicator.rsi_14) if indicator.rsi_14 else None,
            macd=float(indicator.macd) if indicator.macd else None,
            macd_signal=float(indicator.macd_signal) if indicator.macd_signal else None,
            bollinger_upper=float(indicator.bollinger_upper) if indicator.bollinger_upper else None,
            bollinger_middle=float(indicator.bollinger_middle) if indicator.bollinger_middle else None,
            bollinger_lower=float(indicator.bollinger_lower) if indicator.bollinger_lower else None,
        )

    @strawberry.field
    async def latest_news(
        self,
        symbol: str,
        limit: int = 5,
        info: strawberry.Info = None
    ) -> List[News]:
        """Get latest news for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(NewsArticle)
            .where(NewsArticle.symbol == symbol)
            .order_by(desc(NewsArticle.timestamp))
            .limit(limit)
        )
        result = await db.execute(stmt)
        articles = result.scalars().all()

        return [
            News(
                headline=article.headline,
                content=article.content[:200] + "..." if len(article.content) > 200 else article.content,
                source=article.source,
                timestamp=article.timestamp,
                sentiment=float(article.sentiment),
                url=article.url
            )
            for article in articles
        ]

    @strawberry.field
    async def sentiment(
        self,
        symbol: str,
        info: strawberry.Info = None
    ) -> Optional[Sentiment]:
        """Get aggregated sentiment for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(SentimentScore)
            .where(SentimentScore.symbol == symbol)
            .order_by(desc(SentimentScore.timestamp))
            .limit(1)
        )
        result = await db.execute(stmt)
        sentiment = result.scalar_one_or_none()

        if not sentiment:
            return None

        return Sentiment(
            symbol=sentiment.symbol,
            score=float(sentiment.score),
            label=sentiment.label,
            timestamp=sentiment.timestamp,
            news_count=sentiment.news_count or 0,
            social_count=sentiment.social_count or 0
        )

    @strawberry.field
    async def trading_signal(
        self,
        symbol: str,
        info: strawberry.Info = None
    ) -> Optional[TradingSignalType]:
        """Get latest trading signal for a symbol"""
        db: AsyncSession = info.context["db"]

        stmt = (
            select(TradingSignal)
            .where(TradingSignal.symbol == symbol)
            .order_by(desc(TradingSignal.timestamp))
            .limit(1)
        )
        result = await db.execute(stmt)
        signal = result.scalar_one_or_none()

        if not signal:
            return None

        return TradingSignalType(
            symbol=signal.symbol,
            action=signal.action,
            confidence=float(signal.confidence),
            target_price=float(signal.target_price) if signal.target_price else None,
            stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
            timestamp=signal.timestamp,
            reasoning=signal.reasoning
        )

    @strawberry.field
    async def alerts(
        self,
        symbol: Optional[str] = None,
        limit: int = 10,
        info: strawberry.Info = None
    ) -> List[Alert]:
        """Get recent alerts"""
        db: AsyncSession = info.context["db"]

        stmt = select(MarketAlert).order_by(desc(MarketAlert.timestamp)).limit(limit)

        if symbol:
            stmt = stmt.where(MarketAlert.symbol == symbol)

        result = await db.execute(stmt)
        alerts = result.scalars().all()

        return [
            Alert(
                alert_type=alert.alert_type,
                symbol=alert.symbol,
                message=alert.message,
                severity=alert.severity,
                timestamp=alert.timestamp,
                price_at_alert=float(alert.price_at_alert) if alert.price_at_alert else None
            )
            for alert in alerts
        ]

    @strawberry.field
    async def market_summary(
        self,
        symbol: str,
        info: strawberry.Info = None
    ) -> MarketSummary:
        """Get complete market summary for a symbol (all data in one query)"""
        # Fetch all data in parallel using the existing resolvers
        latest_price = await self.latest_price(symbol, info)
        indicators = await self.technical_indicators(symbol, info)
        sentiment_data = await self.sentiment(symbol, info)
        signal = await self.trading_signal(symbol, info)
        alerts_data = await self.alerts(symbol, 5, info)
        news_data = await self.latest_news(symbol, 3, info)

        return MarketSummary(
            symbol=symbol,
            latest_price=latest_price,
            indicators=indicators,
            sentiment=sentiment_data,
            latest_signal=signal,
            recent_alerts=alerts_data,
            recent_news=news_data
        )


# GraphQL Mutations
@strawberry.type
class Mutation:
    """GraphQL mutation root"""

    @strawberry.mutation
    async def ask_question(
        self,
        session_id: str,
        user_message: str,
        symbol: Optional[str] = None,
        info: strawberry.Info = None
    ) -> AnalysisResult:
        """Ask a question to the AI assistant"""
        # Import here to avoid circular dependency
        from app.agents.langchain_agent import get_langchain_agent

        agent = get_langchain_agent()

        # Use the agent to answer the question
        answer = await agent.answer_question(user_message, symbol)

        return AnalysisResult(
            answer=answer,
            confidence=0.85,  # Could be calculated from agent internals
            sources=["RAG", "VectorDB", "LiveData"],
            timestamp=datetime.utcnow()
        )


# Create the GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


# Create the GraphQL router
async def get_context():
    """Provide context for GraphQL resolvers"""
    async for db in get_db_session():
        return {"db": db}


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True  # Enable GraphiQL interface for testing
)
