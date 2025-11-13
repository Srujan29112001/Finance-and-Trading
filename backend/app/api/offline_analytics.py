"""
Offline Analytics API
Runs entirely locally without cloud dependencies
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from app.agents.offline_llm import get_offline_analyzer
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class OfflineAnalysisRequest(BaseModel):
    symbol: str
    question: Optional[str] = None
    include_sentiment: bool = True
    include_news: bool = True


class OfflineAnalysisResponse(BaseModel):
    symbol: str
    analysis: str
    model: str
    processing_time_ms: int
    timestamp: str
    mode: str = "offline"


@router.post("/analyze", response_model=OfflineAnalysisResponse)
async def offline_market_analysis(
    request: OfflineAnalysisRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Perform market analysis using offline LLM (no cloud API needed).

    This endpoint runs a local LLM (LLaMA 2, Mistral, etc.) to analyze
    market data without sending anything to the cloud.

    Benefits:
    - Complete privacy (data never leaves your server)
    - No API costs
    - Works without internet
    - Consistent availability

    Example:
    ```json
    {
        "symbol": "AAPL",
        "question": "Should I buy or sell based on current data?",
        "include_sentiment": true,
        "include_news": true
    }
    ```
    """
    try:
        start_time = datetime.utcnow()

        # Get offline analyzer
        analyzer = get_offline_analyzer()

        # Fetch market data
        price_data = await _get_price_data(db, request.symbol)
        if not price_data:
            raise HTTPException(
                status_code=404,
                detail=f"No price data found for {request.symbol}"
            )

        # Fetch sentiment if requested
        sentiment_data = None
        if request.include_sentiment:
            sentiment_data = await _get_sentiment_data(db, request.symbol)

        # Fetch news if requested
        news_data = None
        if request.include_news:
            news_data = await _get_news_data(request.symbol)

        # Perform analysis
        if request.question:
            # Answer specific question
            context = _build_context(price_data, sentiment_data, news_data)
            analysis = await analyzer.answer_question(
                question=request.question,
                context=context
            )
        else:
            # General market analysis
            analysis = await analyzer.analyze_market_data(
                symbol=request.symbol,
                price_data=price_data,
                sentiment_data=sentiment_data,
                news_data=news_data
            )

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        return OfflineAnalysisResponse(
            symbol=request.symbol,
            analysis=analysis,
            model=analyzer.llm.model_name,
            processing_time_ms=processing_time,
            timestamp=end_time.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in offline analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def offline_chat(
    message: str,
    context: Optional[str] = None
):
    """
    Chat with offline LLM about markets.

    Pure offline conversational interface without cloud APIs.

    Example:
    ```bash
    curl -X POST "http://localhost:8000/api/offline/chat" \
      -H "Content-Type: application/json" \
      -d '{"message": "Explain what a bull market is"}'
    ```
    """
    try:
        analyzer = get_offline_analyzer()

        response = await analyzer.answer_question(
            question=message,
            context=context
        )

        return {
            "message": message,
            "response": response,
            "model": analyzer.llm.model_name,
            "mode": "offline",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in offline chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def offline_engine_status():
    """
    Check status of offline LLM engine.

    Returns information about which model is loaded and ready.
    """
    try:
        analyzer = get_offline_analyzer()

        is_loaded = analyzer.llm.model is not None

        return {
            "status": "ready" if is_loaded else "not_loaded",
            "model_name": analyzer.llm.model_name,
            "backend": analyzer.llm.backend,
            "model_path": analyzer.llm.model_path,
            "loaded": is_loaded,
            "capabilities": {
                "market_analysis": True,
                "q_and_a": True,
                "no_internet_required": True,
                "privacy": "complete"
            },
            "performance": {
                "typical_response_time": "5-30 seconds (depends on hardware)",
                "memory_usage": "4-8GB RAM (for 7B model)",
                "gpu_recommended": True
            }
        }

    except Exception as e:
        logger.error(f"Error checking offline engine status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "recommendation": "Install requirements: pip install -r requirements-vlm.txt"
        }


@router.get("/models")
async def list_offline_models():
    """
    List available offline LLM models.

    Shows which models can be used for offline analytics.
    """
    return {
        "available_models": [
            {
                "name": "llama2-7b",
                "description": "Meta's LLaMA 2 Chat (7B)",
                "size": "3.5GB (4-bit quantized GGUF)",
                "quality": "Good",
                "speed": "Fast",
                "download": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF",
                "recommended": True
            },
            {
                "name": "llama2-13b",
                "description": "Meta's LLaMA 2 Chat (13B)",
                "size": "7GB (4-bit quantized)",
                "quality": "Better",
                "speed": "Medium",
                "download": "https://huggingface.co/TheBloke/Llama-2-13B-Chat-GGUF",
                "recommended": False
            },
            {
                "name": "mistral-7b",
                "description": "Mistral 7B Instruct",
                "size": "4GB (4-bit quantized)",
                "quality": "Excellent",
                "speed": "Fast",
                "download": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
                "recommended": True
            }
        ],
        "setup_instructions": {
            "step_1": "Download a .gguf model file from HuggingFace (links above)",
            "step_2": "Place it in /models/offline_llm/ directory",
            "step_3": "Restart the backend service",
            "step_4": "Model loads automatically on first request"
        },
        "requirements": {
            "cpu": "Any modern CPU (8+ cores recommended)",
            "ram": "8GB minimum, 16GB recommended",
            "gpu": "Optional but highly recommended (NVIDIA with CUDA)",
            "disk": "5-10GB free space per model"
        }
    }


@router.get("/compare-modes")
async def compare_online_vs_offline():
    """
    Compare online (cloud API) vs offline (local) modes.

    Helps users decide which mode to use.
    """
    return {
        "online_mode": {
            "pros": [
                "Best quality (GPT-4, Claude, etc.)",
                "Fastest response time",
                "No local resources needed",
                "Latest models"
            ],
            "cons": [
                "Costs money (API fees)",
                "Requires internet",
                "Privacy concerns (data sent to cloud)",
                "Rate limits"
            ],
            "use_when": [
                "Need highest quality analysis",
                "Don't have GPU",
                "Cost is not a concern"
            ]
        },
        "offline_mode": {
            "pros": [
                "Complete privacy (data never leaves your server)",
                "No ongoing costs",
                "Works without internet",
                "No rate limits",
                "Predictable performance"
            ],
            "cons": [
                "Requires powerful hardware",
                "Slower response time",
                "Slightly lower quality than GPT-4",
                "Initial setup needed"
            ],
            "use_when": [
                "Privacy is critical",
                "Have GPU available",
                "Want to avoid API costs",
                "Need guaranteed availability"
            ]
        },
        "recommendation": {
            "for_development": "Online (easier setup)",
            "for_production": "Offline (lower cost, better privacy)",
            "for_high_volume": "Offline (no rate limits)",
            "for_best_quality": "Online with GPT-4"
        }
    }


# Helper functions

async def _get_price_data(db: AsyncSession, symbol: str) -> Optional[Dict[str, Any]]:
    """Get latest price data for symbol."""
    try:
        from app.models.market import LatestStockPrice
        from sqlalchemy import select

        query = select(LatestStockPrice).where(
            LatestStockPrice.symbol == symbol.upper()
        )
        result = await db.execute(query)
        price = result.scalar_one_or_none()

        if not price:
            return None

        return {
            "symbol": symbol,
            "current_price": float(price.close),
            "open": float(price.open),
            "high": float(price.high),
            "low": float(price.low),
            "volume": int(price.volume),
            "timestamp": price.timestamp
        }

    except Exception as e:
        logger.error(f"Error fetching price data: {e}")
        return None


async def _get_sentiment_data(db: AsyncSession, symbol: str) -> Optional[Dict[str, Any]]:
    """Get sentiment data for symbol."""
    try:
        from app.models.sentiment import SentimentScore
        from sqlalchemy import select, func, and_
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(hours=24)

        query = select(
            func.avg(SentimentScore.sentiment_score).label("avg"),
            func.count(SentimentScore.id).label("count")
        ).where(
            and_(
                SentimentScore.symbol == symbol.upper(),
                SentimentScore.timestamp >= since
            )
        )

        result = await db.execute(query)
        row = result.first()

        if not row or row.count == 0:
            return None

        avg_sentiment = float(row.avg)
        if avg_sentiment > 0.1:
            label = "positive"
        elif avg_sentiment < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return {
            "avg_sentiment": avg_sentiment,
            "sentiment_label": label,
            "sample_size": row.count
        }

    except Exception as e:
        logger.error(f"Error fetching sentiment: {e}")
        return None


async def _get_news_data(symbol: str, limit: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Get recent news for symbol."""
    try:
        from app.database import get_mongodb

        mongodb = get_mongodb()
        news_collection = mongodb["news_articles"]

        articles = news_collection.find(
            {"symbol": symbol.upper()}
        ).sort("published_at", -1).limit(limit)

        return [
            {
                "headline": article.get("headline", ""),
                "source": article.get("source", ""),
                "published_at": article.get("published_at")
            }
            for article in articles
        ]

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return None


def _build_context(
    price_data: Dict[str, Any],
    sentiment_data: Optional[Dict[str, Any]],
    news_data: Optional[List[Dict[str, Any]]]
) -> str:
    """Build context string for analysis."""
    context = f"Stock: {price_data['symbol']}\n"
    context += f"Price: ${price_data['current_price']}\n"
    context += f"Volume: {price_data['volume']:,}\n"

    if sentiment_data:
        context += f"Sentiment: {sentiment_data['sentiment_label']} ({sentiment_data['avg_sentiment']:.2f})\n"

    if news_data:
        context += "\nRecent News:\n"
        for article in news_data:
            context += f"- {article['headline']}\n"

    return context
