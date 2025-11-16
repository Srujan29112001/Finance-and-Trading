"""
GraphQL Schema for Finance Analytics & Trading Co-Pilot

Provides a unified GraphQL interface for querying market data, analytics,
and AI-powered insights using Strawberry GraphQL.
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# Import database and services
from app.database import get_postgres_session, get_mongodb, get_neo4j_driver
from sqlalchemy import text
import asyncio


@strawberry.type
class PriceData:
    """Stock price data point"""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@strawberry.type
class NewsArticle:
    """News article with sentiment"""
    headline: str
    content: str
    source: str
    sentiment_score: float
    sentiment_label: str
    published_at: datetime
    symbol: Optional[str] = None


@strawberry.type
class TradingSignal:
    """ML-generated trading signal"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    rationale: Optional[str] = None
    generated_at: datetime


@strawberry.type
class SentimentData:
    """Aggregated sentiment information"""
    symbol: str
    overall_score: float
    news_sentiment: float
    social_sentiment: float
    label: str
    sample_size: int


@strawberry.type
class MarketAlert:
    """Real-time market alert"""
    id: int
    symbol: str
    alert_type: str
    severity: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime


@strawberry.type
class TechnicalIndicator:
    """Technical analysis indicators"""
    symbol: str
    date: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None


@strawberry.type
class PortfolioPosition:
    """User portfolio position"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float


@strawberry.type
class MarketSummary:
    """Complete market summary for a symbol"""
    symbol: str
    latest_price: Optional[PriceData] = None
    sentiment: Optional[SentimentData] = None
    signals: List[TradingSignal] = strawberry.field(default_factory=list)
    alerts: List[MarketAlert] = strawberry.field(default_factory=list)
    indicators: Optional[TechnicalIndicator] = None


@strawberry.type
class ChatResponse:
    """AI assistant response"""
    message: str
    confidence: float
    sources: List[str] = strawberry.field(default_factory=list)
    timestamp: datetime


@strawberry.type
class KnowledgeGraphRelationship:
    """Graph database relationship"""
    source_entity: str
    relationship_type: str
    target_entity: str
    properties: Optional[str] = None  # JSON string


@strawberry.type
class Query:
    """GraphQL Query Root"""

    @strawberry.field
    async def price_history(
        self,
        symbol: str,
        limit: int = 100,
        start_date: Optional[datetime] = None
    ) -> List[PriceData]:
        """Get historical price data for a symbol"""
        async with get_postgres_session() as session:
            query = """
                SELECT timestamp, symbol, open, high, low, close, volume
                FROM stock_prices
                WHERE symbol = :symbol
            """
            params = {"symbol": symbol}

            if start_date:
                query += " AND timestamp >= :start_date"
                params["start_date"] = start_date

            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit

            result = await session.execute(text(query), params)
            rows = result.fetchall()

            return [
                PriceData(
                    timestamp=row[0],
                    symbol=row[1],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=int(row[6])
                )
                for row in rows
            ]

    @strawberry.field
    async def latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the most recent price for a symbol"""
        prices = await self.price_history(symbol=symbol, limit=1)
        return prices[0] if prices else None

    @strawberry.field
    async def latest_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> List[NewsArticle]:
        """Get recent news articles"""
        mongo_db = await get_mongodb()
        collection = mongo_db["news_articles"]

        query = {}
        if symbol:
            query["symbol"] = symbol

        cursor = collection.find(query).sort("published_at", -1).limit(limit)
        articles = await cursor.to_list(length=limit)

        return [
            NewsArticle(
                headline=article.get("headline", ""),
                content=article.get("content", ""),
                source=article.get("source", ""),
                sentiment_score=float(article.get("sentiment_score", 0.0)),
                sentiment_label=article.get("sentiment_label", "neutral"),
                published_at=article.get("published_at", datetime.utcnow()),
                symbol=article.get("symbol")
            )
            for article in articles
        ]

    @strawberry.field
    async def trading_signals(
        self,
        symbol: str,
        limit: int = 10
    ) -> List[TradingSignal]:
        """Get recent trading signals from RL agent"""
        async with get_postgres_session() as session:
            query = """
                SELECT symbol, action, confidence, target_price,
                       stop_loss, rationale, generated_at
                FROM trading_signals
                WHERE symbol = :symbol
                ORDER BY generated_at DESC
                LIMIT :limit
            """
            result = await session.execute(
                text(query),
                {"symbol": symbol, "limit": limit}
            )
            rows = result.fetchall()

            return [
                TradingSignal(
                    symbol=row[0],
                    action=row[1],
                    confidence=float(row[2]),
                    target_price=float(row[3]) if row[3] else None,
                    stop_loss=float(row[4]) if row[4] else None,
                    rationale=row[5],
                    generated_at=row[6]
                )
                for row in rows
            ]

    @strawberry.field
    async def sentiment(self, symbol: str) -> Optional[SentimentData]:
        """Get aggregated sentiment for a symbol"""
        async with get_postgres_session() as session:
            query = """
                SELECT symbol, overall_score, news_sentiment, social_sentiment,
                       sentiment_label, sample_size
                FROM sentiment_scores
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT 1
            """
            result = await session.execute(text(query), {"symbol": symbol})
            row = result.fetchone()

            if not row:
                return None

            return SentimentData(
                symbol=row[0],
                overall_score=float(row[1]),
                news_sentiment=float(row[2]),
                social_sentiment=float(row[3]),
                label=row[4],
                sample_size=int(row[5])
            )

    @strawberry.field
    async def market_alerts(
        self,
        symbol: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 20
    ) -> List[MarketAlert]:
        """Get recent market alerts"""
        async with get_postgres_session() as session:
            query = "SELECT id, symbol, alert_type, severity, message, value, threshold, created_at FROM market_alerts WHERE 1=1"
            params = {}

            if symbol:
                query += " AND symbol = :symbol"
                params["symbol"] = symbol

            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity

            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit

            result = await session.execute(text(query), params)
            rows = result.fetchall()

            return [
                MarketAlert(
                    id=row[0],
                    symbol=row[1],
                    alert_type=row[2],
                    severity=row[3],
                    message=row[4],
                    value=float(row[5]) if row[5] else None,
                    threshold=float(row[6]) if row[6] else None,
                    created_at=row[7]
                )
                for row in rows
            ]

    @strawberry.field
    async def technical_indicators(
        self,
        symbol: str
    ) -> Optional[TechnicalIndicator]:
        """Get latest technical indicators"""
        async with get_postgres_session() as session:
            query = """
                SELECT symbol, date, sma_20, sma_50, rsi_14, macd,
                       macd_signal, bollinger_upper, bollinger_lower
                FROM technical_indicators
                WHERE symbol = :symbol
                ORDER BY date DESC
                LIMIT 1
            """
            result = await session.execute(text(query), {"symbol": symbol})
            row = result.fetchone()

            if not row:
                return None

            return TechnicalIndicator(
                symbol=row[0],
                date=row[1],
                sma_20=float(row[2]) if row[2] else None,
                sma_50=float(row[3]) if row[3] else None,
                rsi_14=float(row[4]) if row[4] else None,
                macd=float(row[5]) if row[5] else None,
                macd_signal=float(row[6]) if row[6] else None,
                bollinger_upper=float(row[7]) if row[7] else None,
                bollinger_lower=float(row[8]) if row[8] else None
            )

    @strawberry.field
    async def market_summary(self, symbol: str) -> MarketSummary:
        """Get comprehensive market summary for a symbol"""
        # Run queries in parallel for efficiency
        latest_price_task = self.latest_price(symbol)
        sentiment_task = self.sentiment(symbol)
        signals_task = self.trading_signals(symbol, limit=5)
        alerts_task = self.market_alerts(symbol=symbol, limit=5)
        indicators_task = self.technical_indicators(symbol)

        # Gather all results
        results = await asyncio.gather(
            latest_price_task,
            sentiment_task,
            signals_task,
            alerts_task,
            indicators_task,
            return_exceptions=True
        )

        return MarketSummary(
            symbol=symbol,
            latest_price=results[0] if not isinstance(results[0], Exception) else None,
            sentiment=results[1] if not isinstance(results[1], Exception) else None,
            signals=results[2] if not isinstance(results[2], Exception) else [],
            alerts=results[3] if not isinstance(results[3], Exception) else [],
            indicators=results[4] if not isinstance(results[4], Exception) else None
        )

    @strawberry.field
    async def knowledge_graph_query(
        self,
        entity: str,
        relationship_type: Optional[str] = None
    ) -> List[KnowledgeGraphRelationship]:
        """Query the knowledge graph for relationships"""
        driver = await get_neo4j_driver()

        cypher_query = """
        MATCH (a)-[r]->(b)
        WHERE a.name = $entity
        """
        params = {"entity": entity}

        if relationship_type:
            cypher_query = cypher_query.replace("[r]", f"[r:{relationship_type}]")

        cypher_query += " RETURN a.name, type(r), b.name, properties(r) LIMIT 50"

        async with driver.session() as session:
            result = await session.run(cypher_query, params)
            records = await result.data()

        return [
            KnowledgeGraphRelationship(
                source_entity=record.get("a.name", ""),
                relationship_type=record.get("type(r)", ""),
                target_entity=record.get("b.name", ""),
                properties=str(record.get("properties(r)", {}))
            )
            for record in records
        ]


@strawberry.type
class Mutation:
    """GraphQL Mutation Root"""

    @strawberry.mutation
    async def ask_ai(
        self,
        message: str,
        symbol: Optional[str] = None
    ) -> ChatResponse:
        """Ask the AI assistant a question"""
        from app.agents.hybrid_orchestrator import get_orchestrator

        orchestrator = await get_orchestrator()

        context = {}
        if symbol:
            context["symbol"] = symbol

        response = await orchestrator.process_query(message, context)

        return ChatResponse(
            message=response.get("response", ""),
            confidence=response.get("confidence", 0.0),
            sources=response.get("sources", []),
            timestamp=datetime.utcnow()
        )

    @strawberry.mutation
    async def generate_trading_signal(
        self,
        symbol: str
    ) -> TradingSignal:
        """Generate a new trading signal using the RL agent"""
        from app.agents.rl_agent import get_rl_agent

        rl_agent = await get_rl_agent()
        signal = await rl_agent.generate_signal(symbol)

        return TradingSignal(
            symbol=signal["symbol"],
            action=signal["action"],
            confidence=signal["confidence"],
            target_price=signal.get("target_price"),
            stop_loss=signal.get("stop_loss"),
            rationale=signal.get("rationale"),
            generated_at=datetime.utcnow()
        )


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
