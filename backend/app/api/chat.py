"""
AI Chat Assistant API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import uuid

from app.agents.langchain_agent import FinanceCopilotAgent
from app.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# Pydantic models
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    symbol: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    sources: Optional[List[Dict[str, Any]]] = []
    tools_used: Optional[List[str]] = []
    confidence: Optional[float] = None
    timestamp: datetime


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    last_updated: datetime


# Initialize the agent (will be lazy-loaded)
copilot_agent = None


def get_copilot_agent() -> FinanceCopilotAgent:
    """Get or initialize the copilot agent."""
    global copilot_agent
    if copilot_agent is None:
        copilot_agent = FinanceCopilotAgent()
    return copilot_agent


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Ask the AI Co-Pilot a question about markets, stocks, or trading.

    The AI agent uses:
    - RAG (Retrieval-Augmented Generation) to fetch relevant data
    - GraphRAG for relationship-based queries
    - Real-time market data
    - Sentiment analysis
    - RL trading signals

    Examples:
    - "Why did TSLA spike at 10:03 today?"
    - "What's the sentiment on Apple stock?"
    - "Should I buy Tesla now?"
    - "Compare earnings of AAPL and MSFT"
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        logger.info(f"Chat request - Session: {session_id}, Message: {request.message}")

        # Get the copilot agent
        agent = get_copilot_agent()

        # Process the query with context
        result = await agent.process_query(
            query=request.message,
            session_id=session_id,
            symbol=request.symbol,
            context=request.context
        )

        # Save conversation to database
        from app.models.chat import LLMConversation
        conversation = LLMConversation(
            session_id=session_id,
            user_id=request.context.get("user_id") if request.context else None,
            user_message=request.message,
            assistant_response=result["response"],
            context_used=result.get("context"),
            tools_used=result.get("tools_used", []),
            response_time_ms=result.get("response_time_ms"),
            timestamp=datetime.utcnow()
        )
        db.add(conversation)
        await db.commit()

        return ChatResponse(
            session_id=session_id,
            message=request.message,
            response=result["response"],
            sources=result.get("sources", []),
            tools_used=result.get("tools_used", []),
            confidence=result.get("confidence"),
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session)
):
    """Get conversation history for a session."""
    try:
        from app.models.chat import LLMConversation
        from sqlalchemy import select

        query = select(LLMConversation).where(
            LLMConversation.session_id == session_id
        ).order_by(LLMConversation.timestamp.asc()).limit(limit)

        result = await db.execute(query)
        conversations = result.scalars().all()

        if not conversations:
            raise HTTPException(status_code=404, detail="Session not found")

        # Build message history
        messages = []
        for conv in conversations:
            messages.append(ChatMessage(
                role="user",
                content=conv.user_message,
                timestamp=conv.timestamp
            ))
            messages.append(ChatMessage(
                role="assistant",
                content=conv.assistant_response,
                timestamp=conv.timestamp
            ))

        return ConversationHistory(
            session_id=session_id,
            messages=messages,
            created_at=conversations[0].created_at,
            last_updated=conversations[-1].timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a conversation session."""
    try:
        from app.models.chat import LLMConversation
        from sqlalchemy import delete

        query = delete(LLMConversation).where(
            LLMConversation.session_id == session_id
        )
        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": f"Session {session_id} deleted", "deleted_count": result.rowcount}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_market_event(
    symbol: str,
    event_time: datetime,
    question: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Analyze a specific market event using AI.

    Example: Analyze why a stock spiked at a specific time.
    """
    try:
        agent = get_copilot_agent()

        # Default question if not provided
        if not question:
            question = f"Why did {symbol} have unusual activity at {event_time.strftime('%H:%M')}?"

        # Add context about the specific time
        context = {
            "symbol": symbol,
            "event_time": event_time.isoformat(),
            "analysis_type": "event_analysis"
        }

        result = await agent.process_query(
            query=question,
            symbol=symbol,
            context=context
        )

        return {
            "symbol": symbol,
            "event_time": event_time,
            "question": question,
            "analysis": result["response"],
            "sources": result.get("sources", []),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error analyzing market event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize-news")
async def summarize_news(
    symbol: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db_session)
):
    """Summarize recent news for a symbol using AI."""
    try:
        agent = get_copilot_agent()

        question = f"Summarize the key news and sentiment for {symbol} from the last {hours} hours."

        result = await agent.process_query(
            query=question,
            symbol=symbol,
            context={"hours": hours, "analysis_type": "news_summary"}
        )

        return {
            "symbol": symbol,
            "hours": hours,
            "summary": result["response"],
            "sources": result.get("sources", []),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error summarizing news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities():
    """Get information about the AI assistant's capabilities."""
    return {
        "features": {
            "rag": "Retrieval-Augmented Generation from financial documents",
            "graph_rag": "Knowledge graph queries for relationship-based insights",
            "real_time_data": "Access to live market data and prices",
            "sentiment_analysis": "News and social media sentiment tracking",
            "technical_analysis": "Technical indicators and chart patterns",
            "rl_signals": "Reinforcement learning trading recommendations",
            "behavioral_analytics": "Trader psychology and risk warnings"
        },
        "data_sources": [
            "Real-time price data",
            "News articles and reports",
            "Social media sentiment",
            "Earnings reports",
            "Technical indicators",
            "Knowledge graph relationships"
        ],
        "supported_queries": [
            "Price movement analysis",
            "Market event explanations",
            "Sentiment summaries",
            "Trading recommendations",
            "Comparative analysis",
            "Risk assessment",
            "Portfolio insights"
        ]
    }
