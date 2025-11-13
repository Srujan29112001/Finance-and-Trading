"""Alert Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class MarketAlert(Base):
    __tablename__ = "market_alerts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metadata = Column(JSONB)
    timestamp = Column(DateTime, nullable=False, index=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
