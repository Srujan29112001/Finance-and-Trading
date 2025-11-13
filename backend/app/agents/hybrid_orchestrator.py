"""
Smart Hybrid Agent Orchestrator
Manages online (LLM + VLM) and offline models with intelligent fallback

Priority:
1. Both OpenAI LLM + VLM working → Use both (best quality)
2. Only one working → Use available + inform user
3. Neither working → Use offline mode + inform user
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from loguru import logger
from enum import Enum

# Import all agents
from app.agents.langchain_agent import FinanceCopilotAgent
from app.agents.vlm_agent import VLMAgent, get_vlm_agent
from app.agents.offline_llm import OfflineFinanceAnalyzer, get_offline_analyzer
from app.config import settings


class ModelStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"


class ModelMode(Enum):
    """Operating mode based on available models."""
    FULL_ONLINE = "full_online"  # Both LLM + VLM online
    LLM_ONLY = "llm_only"  # Only LLM online
    VLM_ONLY = "vlm_only"  # Only VLM online
    OFFLINE = "offline"  # All offline


class HybridAgentOrchestrator:
    """
    Intelligent orchestrator that manages multiple AI models with fallback.

    Automatically detects which models are available and uses the best combination.
    Provides clear feedback about which models are being used.
    """

    def __init__(self):
        """Initialize the orchestrator and check model availability."""
        self.llm_status = ModelStatus.NOT_CONFIGURED
        self.vlm_status = ModelStatus.NOT_CONFIGURED
        self.offline_status = ModelStatus.NOT_CONFIGURED

        # Model instances (lazy loaded)
        self._online_llm_agent = None
        self._vlm_agent = None
        self._offline_analyzer = None

        # Check availability
        self._check_model_availability()

        # Determine operating mode
        self.mode = self._determine_mode()

        logger.info(f"✓ Hybrid Orchestrator initialized - Mode: {self.mode.value}")
        self._log_status()

    def _check_model_availability(self):
        """Check which models are available."""

        # Check Online LLM (OpenAI)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith('sk-'):
            try:
                import openai
                openai.api_key = settings.OPENAI_API_KEY
                # Quick test
                self.llm_status = ModelStatus.AVAILABLE
                logger.info("✓ OpenAI LLM: Available")
            except Exception as e:
                self.llm_status = ModelStatus.ERROR
                logger.warning(f"✗ OpenAI LLM: Error - {e}")
        else:
            self.llm_status = ModelStatus.NOT_CONFIGURED
            logger.info("○ OpenAI LLM: Not configured (no API key)")

        # Check VLM (GPT-4 Vision)
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith('sk-'):
            try:
                # VLM uses same OpenAI key
                self.vlm_status = ModelStatus.AVAILABLE
                logger.info("✓ VLM (GPT-4 Vision): Available")
            except Exception as e:
                self.vlm_status = ModelStatus.ERROR
                logger.warning(f"✗ VLM: Error - {e}")
        else:
            self.vlm_status = ModelStatus.NOT_CONFIGURED
            logger.info("○ VLM: Not configured (no API key)")

        # Check Offline Models
        try:
            # Check if offline dependencies are installed
            import llama_cpp
            self.offline_status = ModelStatus.AVAILABLE
            logger.info("✓ Offline LLM: Available")
        except ImportError:
            self.offline_status = ModelStatus.NOT_INSTALLED
            logger.info("○ Offline LLM: Not installed (install requirements-vlm.txt)")

    def _determine_mode(self) -> ModelMode:
        """Determine the best operating mode based on availability."""

        llm_ok = self.llm_status == ModelStatus.AVAILABLE
        vlm_ok = self.vlm_status == ModelStatus.AVAILABLE
        offline_ok = self.offline_status == ModelStatus.AVAILABLE

        if llm_ok and vlm_ok:
            return ModelMode.FULL_ONLINE
        elif llm_ok and not vlm_ok:
            return ModelMode.LLM_ONLY
        elif vlm_ok and not llm_ok:
            return ModelMode.VLM_ONLY
        elif offline_ok:
            return ModelMode.OFFLINE
        else:
            # Nothing available - will use mock responses
            return ModelMode.OFFLINE

    def _log_status(self):
        """Log the current status of all models."""
        status_msg = f"""
╔══════════════════════════════════════════════════════════════╗
║           FINANCE AI MODELS STATUS                           ║
╠══════════════════════════════════════════════════════════════╣
║ Online LLM (OpenAI):     {self._status_symbol(self.llm_status)} {self.llm_status.value.ljust(20)} ║
║ VLM (GPT-4 Vision):      {self._status_symbol(self.vlm_status)} {self.vlm_status.value.ljust(20)} ║
║ Offline LLM:             {self._status_symbol(self.offline_status)} {self.offline_status.value.ljust(20)} ║
╠══════════════════════════════════════════════════════════════╣
║ Operating Mode:          {self.mode.value.upper().ljust(28)} ║
╚══════════════════════════════════════════════════════════════╝
        """
        logger.info(status_msg)

    def _status_symbol(self, status: ModelStatus) -> str:
        """Get emoji symbol for status."""
        if status == ModelStatus.AVAILABLE:
            return "✅"
        elif status == ModelStatus.NOT_CONFIGURED:
            return "⚙️"
        elif status == ModelStatus.NOT_INSTALLED:
            return "📦"
        else:
            return "❌"

    def _get_status_message(self) -> str:
        """Get human-readable status message for user."""
        if self.mode == ModelMode.FULL_ONLINE:
            return "🟢 Using **OpenAI GPT-4 + Vision** (Best Quality)"

        elif self.mode == ModelMode.LLM_ONLY:
            return "🟡 Using **OpenAI GPT-4** only. VLM not available - chart analysis limited."

        elif self.mode == ModelMode.VLM_ONLY:
            return "🟡 Using **GPT-4 Vision** only. Text analysis will be limited."

        elif self.mode == ModelMode.OFFLINE:
            offline_available = self.offline_status == ModelStatus.AVAILABLE
            if offline_available:
                return "🔵 Using **Offline Mode** (Local LLaMA/Mistral). No cloud APIs configured."
            else:
                return "⚪ **Limited Mode**: No models fully available. Using basic analysis."

    async def process_query(
        self,
        query: str,
        symbol: Optional[str] = None,
        include_chart_analysis: bool = False,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query using the best available models.

        Args:
            query: User question
            symbol: Stock symbol (if applicable)
            include_chart_analysis: Whether to include VLM chart analysis
            session_id: Conversation session ID
            context: Additional context

        Returns:
            Response with model status and answer
        """
        start_time = datetime.utcnow()

        # Prepare response
        response = {
            "query": query,
            "symbol": symbol,
            "mode": self.mode.value,
            "status_message": self._get_status_message(),
            "models_used": [],
            "response": "",
            "chart_analysis": None,
            "timestamp": start_time.isoformat()
        }

        try:
            # Mode: Full Online (Best)
            if self.mode == ModelMode.FULL_ONLINE:
                response = await self._process_full_online(
                    query, symbol, include_chart_analysis, session_id, context, response
                )

            # Mode: LLM Only
            elif self.mode == ModelMode.LLM_ONLY:
                response = await self._process_llm_only(
                    query, symbol, include_chart_analysis, session_id, context, response
                )

            # Mode: VLM Only
            elif self.mode == ModelMode.VLM_ONLY:
                response = await self._process_vlm_only(
                    query, symbol, include_chart_analysis, context, response
                )

            # Mode: Offline
            elif self.mode == ModelMode.OFFLINE:
                response = await self._process_offline(
                    query, symbol, include_chart_analysis, context, response
                )

        except Exception as e:
            logger.error(f"Error in process_query: {e}")
            response["error"] = str(e)
            response["response"] = f"Error processing query: {str(e)}"

        # Calculate processing time
        end_time = datetime.utcnow()
        response["processing_time_ms"] = int((end_time - start_time).total_seconds() * 1000)

        return response

    async def _process_full_online(
        self,
        query: str,
        symbol: Optional[str],
        include_chart: bool,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process using both online LLM and VLM."""
        response["models_used"].append("OpenAI GPT-4")

        # Get chart analysis if requested and symbol provided
        chart_analysis = None
        if include_chart and symbol:
            try:
                vlm = get_vlm_agent(model_name="gpt4-vision")
                # Get price data and analyze chart
                price_data = await self._get_price_data(symbol)
                if price_data:
                    chart_result = await vlm.analyze_from_data(
                        price_data=price_data,
                        symbol=symbol,
                        chart_type="candlestick"
                    )
                    chart_analysis = chart_result.get("interpretation")
                    response["models_used"].append("GPT-4 Vision")
                    response["chart_analysis"] = chart_analysis
            except Exception as e:
                logger.error(f"VLM error: {e}")
                chart_analysis = f"Chart analysis unavailable: {str(e)}"

        # Get LLM response
        if self._online_llm_agent is None:
            self._online_llm_agent = FinanceCopilotAgent()

        # Build enhanced context with chart analysis
        enhanced_context = context or {}
        if chart_analysis:
            enhanced_context["chart_analysis"] = chart_analysis

        llm_response = await self._online_llm_agent.process_query(
            query=query,
            session_id=session_id or "default",
            symbol=symbol,
            context=enhanced_context
        )

        response["response"] = llm_response.get("response", "")
        response["tools_used"] = llm_response.get("tools_used", [])
        response["sources"] = llm_response.get("sources", [])

        return response

    async def _process_llm_only(
        self,
        query: str,
        symbol: Optional[str],
        include_chart: bool,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process using only online LLM (no VLM)."""
        response["models_used"].append("OpenAI GPT-4")

        if include_chart:
            response["warning"] = "Chart analysis unavailable - VLM not configured. Using data-only analysis."

        # Use online LLM
        if self._online_llm_agent is None:
            self._online_llm_agent = FinanceCopilotAgent()

        llm_response = await self._online_llm_agent.process_query(
            query=query,
            session_id=session_id or "default",
            symbol=symbol,
            context=context
        )

        response["response"] = llm_response.get("response", "")
        response["tools_used"] = llm_response.get("tools_used", [])

        return response

    async def _process_vlm_only(
        self,
        query: str,
        symbol: Optional[str],
        include_chart: bool,
        context: Optional[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process using only VLM (no LLM)."""
        response["models_used"].append("GPT-4 Vision")
        response["warning"] = "Using VLM only - text analysis limited. OpenAI LLM not available."

        if include_chart and symbol:
            try:
                vlm = get_vlm_agent(model_name="gpt4-vision")
                price_data = await self._get_price_data(symbol)
                if price_data:
                    chart_result = await vlm.analyze_from_data(
                        price_data=price_data,
                        symbol=symbol,
                        chart_type="candlestick",
                        prompt=query  # Use query as prompt
                    )
                    response["response"] = chart_result.get("interpretation", "")
                    response["chart_analysis"] = chart_result.get("interpretation")
                else:
                    response["response"] = "No price data available for chart analysis."
            except Exception as e:
                logger.error(f"VLM error: {e}")
                response["response"] = f"VLM analysis error: {str(e)}"
        else:
            response["response"] = "VLM requires a symbol and chart analysis enabled."

        return response

    async def _process_offline(
        self,
        query: str,
        symbol: Optional[str],
        include_chart: bool,
        context: Optional[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process using offline models."""

        if self.offline_status == ModelStatus.AVAILABLE:
            response["models_used"].append("Offline LLM (Local)")

            try:
                # Use offline analyzer
                if self._offline_analyzer is None:
                    self._offline_analyzer = get_offline_analyzer()

                if symbol:
                    # Get market data for context
                    price_data = await self._get_price_data(symbol)
                    sentiment_data = await self._get_sentiment_data(symbol)

                    analysis = await self._offline_analyzer.analyze_market_data(
                        symbol=symbol,
                        price_data=price_data or {},
                        sentiment_data=sentiment_data,
                        news_data=None
                    )
                    response["response"] = analysis
                else:
                    # General question
                    answer = await self._offline_analyzer.answer_question(
                        question=query,
                        context=str(context) if context else None
                    )
                    response["response"] = answer

                if include_chart:
                    response["warning"] = "Chart visual analysis not available in offline mode. Using data analysis only."

            except Exception as e:
                logger.error(f"Offline analyzer error: {e}")
                response["response"] = f"Offline mode error: {str(e)}"

        else:
            # No models available at all
            response["models_used"].append("Basic (No AI)")
            response["response"] = self._basic_fallback_response(query, symbol)

        return response

    def _basic_fallback_response(self, query: str, symbol: Optional[str]) -> str:
        """Basic response when no AI models available."""
        msg = "⚠️ **No AI models are currently available.**\n\n"

        if self.llm_status == ModelStatus.NOT_CONFIGURED:
            msg += "- **OpenAI**: Not configured. Add OPENAI_API_KEY to .env file.\n"

        if self.offline_status == ModelStatus.NOT_INSTALLED:
            msg += "- **Offline Models**: Not installed. Run: `pip install -r requirements-vlm.txt`\n"

        msg += "\n**To enable full features:**\n"
        msg += "1. Add OpenAI API key for best quality (recommended)\n"
        msg += "2. OR install offline models for privacy (free)\n"
        msg += "3. OR both for maximum flexibility\n\n"
        msg += f"Your question: *{query}*\n\n"

        if symbol:
            msg += f"For {symbol}, please configure AI models to get detailed analysis."

        return msg

    async def _get_price_data(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Get price data for symbol."""
        try:
            from app.database import async_session_maker
            from app.models.market import StockPrice
            from sqlalchemy import select

            async with async_session_maker() as session:
                query = select(StockPrice).where(
                    StockPrice.symbol == symbol.upper()
                ).order_by(StockPrice.timestamp.desc()).limit(100)

                result = await session.execute(query)
                prices = result.scalars().all()

                if not prices:
                    return None

                return [
                    {
                        "timestamp": p.timestamp,
                        "open": float(p.open),
                        "high": float(p.high),
                        "low": float(p.low),
                        "close": float(p.close),
                        "volume": int(p.volume)
                    }
                    for p in reversed(prices)
                ]

        except Exception as e:
            logger.error(f"Error getting price data: {e}")
            return None

    async def _get_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get sentiment data for symbol."""
        try:
            from app.database import async_session_maker
            from app.models.sentiment import SentimentScore
            from sqlalchemy import select, func, and_
            from datetime import timedelta

            async with async_session_maker() as session:
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

                result = await session.execute(query)
                row = result.first()

                if not row or row.count == 0:
                    return None

                return {
                    "avg_sentiment": float(row.avg) if row.avg else 0.0,
                    "sample_size": row.count
                }

        except Exception as e:
            logger.error(f"Error getting sentiment: {e}")
            return None

    def get_capabilities(self) -> Dict[str, Any]:
        """Get current system capabilities."""
        return {
            "mode": self.mode.value,
            "status_message": self._get_status_message(),
            "available_features": {
                "text_analysis": self.llm_status == ModelStatus.AVAILABLE or self.offline_status == ModelStatus.AVAILABLE,
                "chart_visual_analysis": self.vlm_status == ModelStatus.AVAILABLE,
                "offline_mode": self.offline_status == ModelStatus.AVAILABLE,
                "full_online": self.mode == ModelMode.FULL_ONLINE
            },
            "model_status": {
                "online_llm": self.llm_status.value,
                "vlm": self.vlm_status.value,
                "offline": self.offline_status.value
            },
            "recommendations": self._get_recommendations()
        }

    def _get_recommendations(self) -> List[str]:
        """Get recommendations for improving setup."""
        recommendations = []

        if self.llm_status != ModelStatus.AVAILABLE:
            recommendations.append("Add OPENAI_API_KEY to .env for best quality AI responses")

        if self.vlm_status != ModelStatus.AVAILABLE:
            recommendations.append("OpenAI API key enables chart visual analysis with GPT-4 Vision")

        if self.offline_status != ModelStatus.AVAILABLE:
            recommendations.append("Install offline models (pip install -r requirements-vlm.txt) for privacy and zero cost")

        if not recommendations:
            recommendations.append("✅ All features enabled! You have the best setup.")

        return recommendations


# Singleton instance
_hybrid_orchestrator = None


def get_hybrid_orchestrator() -> HybridAgentOrchestrator:
    """Get the hybrid orchestrator singleton."""
    global _hybrid_orchestrator
    if _hybrid_orchestrator is None:
        _hybrid_orchestrator = HybridAgentOrchestrator()
    return _hybrid_orchestrator
