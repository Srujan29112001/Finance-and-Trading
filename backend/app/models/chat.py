"""Chat and LLM Conversation Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class LLMConversation(Base):
    __tablename__ = "llm_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50))
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    context_used = Column(JSONB)
    tools_used = Column(ARRAY(String))
    response_time_ms = Column(Integer)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class ModelPerformance(Base):
    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(String)
    evaluation_date = Column(String, nullable=False, index=True)
    metadata = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
