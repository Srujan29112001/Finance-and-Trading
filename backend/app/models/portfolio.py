"""Portfolio Models"""

from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, BigInteger
from sqlalchemy.sql import func
from app.database import Base


class UserPortfolio(Base):
    __tablename__ = "user_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)
    quantity = Column(DECIMAL(18, 8), nullable=False)
    avg_purchase_price = Column(DECIMAL(12, 4), nullable=False)
    current_value = Column(DECIMAL(20, 2))
    profit_loss = Column(DECIMAL(20, 2))
    profit_loss_pct = Column(DECIMAL(8, 4))
    last_updated = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())


class RiskMetrics(Base):
    __tablename__ = "risk_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    portfolio_value = Column(DECIMAL(20, 2))
    var_95 = Column(DECIMAL(20, 2))
    var_99 = Column(DECIMAL(20, 2))
    sharpe_ratio = Column(DECIMAL(8, 4))
    sortino_ratio = Column(DECIMAL(8, 4))
    max_drawdown = Column(DECIMAL(8, 4))
    beta = Column(DECIMAL(8, 4))
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class UserBehaviorAnalytics(Base):
    __tablename__ = "user_behavior_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    behavior_type = Column(String(50), nullable=False)
    risk_score = Column(DECIMAL(5, 4))
    trade_frequency_1h = Column(Integer)
    avg_trade_size = Column(DECIMAL(20, 2))
    emotional_state = Column(String(20))
    recommendation = Column(String)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
