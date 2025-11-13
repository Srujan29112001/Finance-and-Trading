"""Trading Models"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)
    confidence = Column(DECIMAL(5, 4), nullable=False)
    price = Column(DECIMAL(12, 4), nullable=False)
    target_price = Column(DECIMAL(12, 4))
    stop_loss = Column(DECIMAL(12, 4))
    reasoning = Column(Text)
    metadata = Column(JSONB)
    timestamp = Column(DateTime, nullable=False, index=True)
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class TradingHistory(Base):
    __tablename__ = "trading_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    price = Column(DECIMAL(12, 4), nullable=False)
    total_value = Column(DECIMAL(20, 2), nullable=False)
    fees = Column(DECIMAL(12, 4))
    timestamp = Column(DateTime, nullable=False, index=True)
    strategy = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
