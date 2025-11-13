"""
LangChain Agent with RAG and GraphRAG for Finance Co-Pilot
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue

from app.config import settings
from app.database import get_qdrant, get_neo4j, get_mongodb
import asyncio


class FinanceCopilotAgent:
    """
    Finance Analytics AI Co-Pilot using LangChain with RAG and GraphRAG.

    Features:
    - RAG: Retrieval-Augmented Generation from vector DB
    - GraphRAG: Knowledge graph queries for relationships
    - Real-time market data integration
    - Sentiment analysis integration
    - RL trading signals integration
    """

    def __init__(self):
        """Initialize the agent with tools and memory."""
        logger.info("Initializing Finance Copilot Agent...")

        # Initialize embeddings for RAG
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )

        # Initialize vector DB client
        self.qdrant_client = get_qdrant()

        # Initialize LLM (using OpenAI or can be replaced with local model)
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=0.3,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback to a simple response if no API key
            logger.warning("No OpenAI API key found. Using mock LLM.")
            self.llm = None

        # Conversation memory
        self.memory = {}

        # Initialize tools
        self.tools = self._create_tools()

        logger.info("✓ Finance Copilot Agent initialized successfully")

    def _create_tools(self) -> List[Tool]:
        """Create tools that the agent can use."""
        tools = [
            Tool(
                name="VectorSearch",
                func=self._vector_search_sync,
                description="""Search for relevant financial documents, news articles, and reports using semantic similarity.
                Input: search query string
                Returns: List of relevant documents with their content and metadata"""
            ),
            Tool(
                name="GetStockPrice",
                func=self._get_stock_price_sync,
                description="""Get current or historical stock price information.
                Input: symbol (e.g., 'AAPL')
                Returns: Latest price data including open, high, low, close, volume"""
            ),
            Tool(
                name="GetSentiment",
                func=self._get_sentiment_sync,
                description="""Get sentiment analysis for a stock from news and social media.
                Input: symbol (e.g., 'TSLA')
                Returns: Aggregated sentiment score and label"""
            ),
            Tool(
                name="GetTradingSignal",
                func=self._get_trading_signal_sync,
                description="""Get AI-generated trading recommendation from the RL agent.
                Input: symbol (e.g., 'AAPL')
                Returns: BUY/SELL/HOLD signal with confidence and reasoning"""
            ),
            Tool(
                name="GraphQuery",
                func=self._graph_query_sync,
                description="""Query the knowledge graph for relationships between entities (companies, events, people).
                Input: Cypher-like query description
                Returns: Related entities and their relationships"""
            ),
            Tool(
                name="GetNewsArticles",
                func=self._get_news_sync,
                description="""Get recent news articles for a specific stock.
                Input: symbol (e.g., 'GOOGL')
                Returns: List of recent news headlines and summaries"""
            )
        ]
        return tools

    def _vector_search_sync(self, query: str) -> str:
        """Synchronous wrapper for vector search."""
        try:
            return asyncio.run(self._vector_search(query))
        except Exception as e:
            return f"Error in vector search: {str(e)}"

    async def _vector_search(self, query: str, limit: int = 5) -> str:
        """
        Search vector database for relevant documents using RAG.
        """
        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_query(query)

            # Search in Qdrant
            results = self.qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit
            )

            if not results:
                return "No relevant documents found."

            # Format results
            formatted_results = []
            for i, hit in enumerate(results, 1):
                payload = hit.payload
                formatted_results.append(
                    f"{i}. [{payload.get('source', 'Unknown')}] {payload.get('title', '')}\n"
                    f"   Content: {payload.get('content', '')[:200]}...\n"
                    f"   Date: {payload.get('date', 'N/A')}\n"
                    f"   Relevance: {hit.score:.2f}"
                )

            return "\n\n".join(formatted_results)

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return f"Error performing vector search: {str(e)}"

    def _get_stock_price_sync(self, symbol: str) -> str:
        """Synchronous wrapper for getting stock price."""
        try:
            return asyncio.run(self._get_stock_price(symbol))
        except Exception as e:
            return f"Error getting stock price: {str(e)}"

    async def _get_stock_price(self, symbol: str) -> str:
        """Get latest stock price from database."""
        try:
            from app.database import async_session_maker
            from app.models.market import LatestStockPrice
            from sqlalchemy import select

            async with async_session_maker() as session:
                query = select(LatestStockPrice).where(
                    LatestStockPrice.symbol == symbol.upper()
                )
                result = await session.execute(query)
                price = result.scalar_one_or_none()

                if not price:
                    return f"No price data available for {symbol}"

                return (
                    f"{symbol.upper()} - Latest Price Data:\n"
                    f"Price: ${float(price.close):.2f}\n"
                    f"Open: ${float(price.open):.2f}\n"
                    f"High: ${float(price.high):.2f}\n"
                    f"Low: ${float(price.low):.2f}\n"
                    f"Volume: {price.volume:,}\n"
                    f"Timestamp: {price.timestamp}"
                )

        except Exception as e:
            logger.error(f"Error getting stock price: {e}")
            return f"Error retrieving stock price for {symbol}: {str(e)}"

    def _get_sentiment_sync(self, symbol: str) -> str:
        """Synchronous wrapper for sentiment."""
        try:
            return asyncio.run(self._get_sentiment(symbol))
        except Exception as e:
            return f"Error getting sentiment: {str(e)}"

    async def _get_sentiment(self, symbol: str) -> str:
        """Get aggregated sentiment for a symbol."""
        try:
            from app.database import async_session_maker
            from app.models.sentiment import SentimentScore
            from sqlalchemy import select, func, and_

            async with async_session_maker() as session:
                # Get recent sentiment (last 24 hours)
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
                    return f"No recent sentiment data available for {symbol}"

                avg_sentiment = float(row.avg) if row.avg else 0.0

                if avg_sentiment > 0.2:
                    label = "Very Positive"
                elif avg_sentiment > 0.05:
                    label = "Positive"
                elif avg_sentiment > -0.05:
                    label = "Neutral"
                elif avg_sentiment > -0.2:
                    label = "Negative"
                else:
                    label = "Very Negative"

                return (
                    f"{symbol.upper()} Sentiment (24h):\n"
                    f"Overall: {label}\n"
                    f"Score: {avg_sentiment:.3f} (range: -1 to +1)\n"
                    f"Based on {row.count} data points"
                )

        except Exception as e:
            logger.error(f"Error getting sentiment: {e}")
            return f"Error retrieving sentiment for {symbol}: {str(e)}"

    def _get_trading_signal_sync(self, symbol: str) -> str:
        """Synchronous wrapper for trading signal."""
        try:
            return asyncio.run(self._get_trading_signal(symbol))
        except Exception as e:
            return f"Error getting trading signal: {str(e)}"

    async def _get_trading_signal(self, symbol: str) -> str:
        """Get latest trading signal from RL agent."""
        try:
            from app.database import async_session_maker
            from app.models.trading import TradingSignal
            from sqlalchemy import select

            async with async_session_maker() as session:
                query = select(TradingSignal).where(
                    TradingSignal.symbol == symbol.upper()
                ).order_by(TradingSignal.timestamp.desc()).limit(1)

                result = await session.execute(query)
                signal = result.scalar_one_or_none()

                if not signal:
                    return f"No trading signals available for {symbol}. The RL agent may need to be run."

                return (
                    f"{symbol.upper()} Trading Signal:\n"
                    f"Action: {signal.signal_type}\n"
                    f"Confidence: {float(signal.confidence):.1%}\n"
                    f"Price: ${float(signal.price):.2f}\n"
                    f"Target: ${float(signal.target_price):.2f}" if signal.target_price else "" + "\n"
                    f"Stop Loss: ${float(signal.stop_loss):.2f}" if signal.stop_loss else "" + "\n"
                    f"Reasoning: {signal.reasoning or 'Based on RL model analysis'}\n"
                    f"Generated: {signal.timestamp}"
                )

        except Exception as e:
            logger.error(f"Error getting trading signal: {e}")
            return f"Error retrieving trading signal for {symbol}: {str(e)}"

    def _graph_query_sync(self, query_description: str) -> str:
        """Synchronous wrapper for graph query."""
        try:
            return asyncio.run(self._graph_query(query_description))
        except Exception as e:
            return f"Error in graph query: {str(e)}"

    async def _graph_query(self, query_description: str) -> str:
        """Query knowledge graph (GraphRAG)."""
        try:
            neo4j_driver = get_neo4j()

            # Simple example query - in production, this would parse the description
            # and generate appropriate Cypher queries
            async with neo4j_driver.session() as session:
                # Example: Get company relationships
                result = await session.run(
                    "MATCH (c:Company) RETURN c.name LIMIT 5"
                )
                records = await result.data()

                if not records:
                    return "Knowledge graph is being populated. No relationships found yet."

                formatted = "Knowledge Graph Entities:\n"
                for record in records:
                    formatted += f"- {record.get('c.name', 'Unknown')}\n"

                return formatted

        except Exception as e:
            logger.error(f"Graph query error: {e}")
            return f"Knowledge graph query in progress. Basic implementation: {str(e)}"

    def _get_news_sync(self, symbol: str) -> str:
        """Synchronous wrapper for news retrieval."""
        try:
            return asyncio.run(self._get_news(symbol))
        except Exception as e:
            return f"Error getting news: {str(e)}"

    async def _get_news(self, symbol: str, limit: int = 5) -> str:
        """Get recent news articles from MongoDB."""
        try:
            mongodb = get_mongodb()
            news_collection = mongodb["news_articles"]

            articles = news_collection.find(
                {"symbol": symbol.upper()}
            ).sort("published_at", -1).limit(limit)

            articles_list = list(articles)

            if not articles_list:
                return f"No recent news found for {symbol}"

            formatted = f"Recent News for {symbol.upper()}:\n\n"
            for i, article in enumerate(articles_list, 1):
                formatted += (
                    f"{i}. {article.get('title', 'No title')}\n"
                    f"   Source: {article.get('source', 'Unknown')}\n"
                    f"   Date: {article.get('published_at', 'Unknown')}\n"
                    f"   Summary: {article.get('summary', 'No summary')[:150]}...\n\n"
                )

            return formatted

        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return f"Error retrieving news for {symbol}: {str(e)}"

    async def process_query(
        self,
        query: str,
        session_id: str,
        symbol: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using the agent with all available tools.
        """
        start_time = time.time()

        try:
            logger.info(f"Processing query for session {session_id}: {query}")

            # If no LLM is configured, use a simple response
            if not self.llm:
                response = await self._simple_response(query, symbol, context)
                return response

            # Create system prompt
            system_prompt = """You are an expert financial analyst and trading assistant.
            You have access to real-time market data, news, sentiment analysis, and AI-powered trading signals.

            When answering questions:
            1. Use the available tools to gather relevant information
            2. Provide data-driven insights with specific numbers and sources
            3. Be concise but thorough in your explanations
            4. Cite your sources when using retrieved information
            5. If asked for trading advice, always include risk warnings

            Your goal is to help users make informed trading and investment decisions."""

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            # For now, use direct LLM call with tool results
            # (Full agent execution would require more complex setup)
            response_text = await self._generate_response_with_tools(query, symbol)

            response_time = int((time.time() - start_time) * 1000)

            return {
                "response": response_text,
                "sources": [],
                "tools_used": ["VectorSearch", "GetStockPrice", "GetSentiment"],
                "confidence": 0.85,
                "response_time_ms": response_time,
                "context": context
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "sources": [],
                "tools_used": [],
                "confidence": 0.0,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "context": context
            }

    async def _generate_response_with_tools(self, query: str, symbol: Optional[str]) -> str:
        """Generate response using tools."""
        # Gather context from tools
        context_parts = []

        # If symbol is mentioned or provided, get relevant data
        if symbol:
            context_parts.append(await self._get_stock_price(symbol))
            context_parts.append(await self._get_sentiment(symbol))
            context_parts.append(await self._get_trading_signal(symbol))

        # Search for relevant documents
        context_parts.append(await self._vector_search(query))

        # Build context string
        context_str = "\n\n---\n\n".join(context_parts)

        # If we have an LLM, use it to generate response
        if self.llm:
            messages = [
                SystemMessage(content="You are a financial analyst. Use the following context to answer the user's question."),
                HumanMessage(content=f"Context:\n{context_str}\n\nQuestion: {query}")
            ]

            response = self.llm.invoke(messages)
            return response.content

        # Fallback response
        return f"Based on the available data:\n\n{context_str}\n\nPlease note: Full AI analysis requires API configuration."

    async def _simple_response(self, query: str, symbol: Optional[str], context: Optional[Dict]) -> Dict[str, Any]:
        """Fallback simple response when no LLM is configured."""
        tools_used = []
        response_parts = ["Based on the available data:\n"]

        if symbol:
            # Get data for the symbol
            price_data = await self._get_stock_price(symbol)
            response_parts.append(f"\n{price_data}")
            tools_used.append("GetStockPrice")

            sentiment_data = await self._get_sentiment(symbol)
            response_parts.append(f"\n{sentiment_data}")
            tools_used.append("GetSentiment")

        response_parts.append("\n\nNote: Full AI analysis with OpenAI requires API key configuration.")

        return {
            "response": "\n".join(response_parts),
            "sources": [],
            "tools_used": tools_used,
            "confidence": 0.7,
            "response_time_ms": 100,
            "context": context
        }
