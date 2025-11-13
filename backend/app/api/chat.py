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
from app.agents.hybrid_orchestrator import get_hybrid_orchestrator
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
    include_chart_analysis: bool = False
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    response: str
    mode: Optional[str] = None
    status_message: Optional[str] = None
    models_used: Optional[List[str]] = []
    chart_analysis: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = []
    tools_used: Optional[List[str]] = []
    confidence: Optional[float] = None
    warning: Optional[str] = None
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
    Ask the AI Co-Pilot a question (SMART MODE - Auto-selects best available models).

    **Intelligent Model Selection:**
    - ✅ Both API keys configured → Uses OpenAI LLM + GPT-4 Vision (best quality)
    - ⚠️ Only LLM configured → Uses OpenAI LLM (informs about VLM unavailable)
    - ⚠️ Only VLM configured → Uses GPT-4 Vision (informs about LLM unavailable)
    - 🔵 No APIs configured → Uses Offline Mode (private, free)

    **The system automatically:**
    1. Detects which models are available
    2. Uses the best combination
    3. Informs you which models are being used
    4. Falls back gracefully if models fail

    **Features:**
    - RAG (Retrieval-Augmented Generation)
    - GraphRAG for relationships
    - Real-time market data
    - Sentiment analysis
    - RL trading signals
    - Chart visual analysis (if VLM available)

    Examples:
    ```json
    {
        "message": "Why did TSLA spike today?",
        "symbol": "TSLA",
        "include_chart_analysis": true
    }
    ```
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        logger.info(f"Smart chat request - Session: {session_id}, Message: {request.message}")

        # Get the hybrid orchestrator (smart model selector)
        orchestrator = get_hybrid_orchestrator()

        # Process with best available models
        result = await orchestrator.process_query(
            query=request.message,
            symbol=request.symbol,
            include_chart_analysis=request.include_chart_analysis,
            session_id=session_id,
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
            mode=result.get("mode"),
            status_message=result.get("status_message"),
            models_used=result.get("models_used", []),
            chart_analysis=result.get("chart_analysis"),
            sources=result.get("sources", []),
            tools_used=result.get("tools_used", []),
            confidence=result.get("confidence"),
            warning=result.get("warning"),
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


@router.get("/model-status")
async def get_model_status():
    """
    Get current model availability and operating mode.

    Returns information about which models (LLM, VLM, Offline) are available
    and what mode the system is currently operating in.
    """
    try:
        orchestrator = get_hybrid_orchestrator()
        capabilities = orchestrator.get_capabilities()

        return {
            "current_mode": capabilities["mode"],
            "status_message": capabilities["status_message"],
            "available_models": capabilities["models_used"],
            "model_details": {
                "llm": {
                    "status": capabilities.get("llm_status", "unknown"),
                    "type": "OpenAI GPT-4" if capabilities.get("llm_status") == "available" else "Not configured"
                },
                "vlm": {
                    "status": capabilities.get("vlm_status", "unknown"),
                    "type": "GPT-4 Vision" if capabilities.get("vlm_status") == "available" else "Not configured"
                },
                "offline": {
                    "status": capabilities.get("offline_status", "unknown"),
                    "type": "LLaMA/Mistral (Local)"
                }
            },
            "features_available": {
                "text_analysis": capabilities.get("llm_status") == "available" or capabilities.get("offline_status") == "available",
                "chart_analysis": capabilities.get("vlm_status") == "available",
                "offline_mode": capabilities.get("offline_status") == "available"
            }
        }
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        return {
            "current_mode": "unknown",
            "status_message": "Error checking model status",
            "error": str(e)
        }


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
            "behavioral_analytics": "Trader psychology and risk warnings",
            "vlm_chart_analysis": "Visual chart interpretation with AI vision",
            "offline_analytics": "100% local processing without cloud APIs"
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
            "Portfolio insights",
            "Chart pattern recognition",
            "Visual technical analysis"
        ]
    }
