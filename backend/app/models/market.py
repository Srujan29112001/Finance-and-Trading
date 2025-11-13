"""Market Data Models"""

from sqlalchemy import Column, Integer, String, Float, BigInteger, DateTime, Date, DECIMAL, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(DECIMAL(12, 4))
    high = Column(DECIMAL(12, 4))
    low = Column(DECIMAL(12, 4))
    close = Column(DECIMAL(12, 4))
    volume = Column(BigInteger)
    vwap = Column(DECIMAL(12, 4))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class LatestStockPrice(Base):
    __tablename__ = "latest_stock_prices"
    __table_args__ = {'extend_existing': True}

    symbol = Column(String(10), primary_key=True)
    timestamp = Column(DateTime)
    open = Column(DECIMAL(12, 4))
    high = Column(DECIMAL(12, 4))
    low = Column(DECIMAL(12, 4))
    close = Column(DECIMAL(12, 4))
    volume = Column(BigInteger)
    vwap = Column(DECIMAL(12, 4))


class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    sma_20 = Column(DECIMAL(12, 4))
    sma_50 = Column(DECIMAL(12, 4))
    ema_12 = Column(DECIMAL(12, 4))
    ema_26 = Column(DECIMAL(12, 4))
    rsi_14 = Column(DECIMAL(8, 4))
    macd = Column(DECIMAL(12, 4))
    macd_signal = Column(DECIMAL(12, 4))
    bollinger_upper = Column(DECIMAL(12, 4))
    bollinger_middle = Column(DECIMAL(12, 4))
    bollinger_lower = Column(DECIMAL(12, 4))
    atr_14 = Column(DECIMAL(12, 4))
    obv = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
    )


class EarningsReport(Base):
    __tablename__ = "earnings_reports"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    quarter = Column(String(10), nullable=False)
    year = Column(Integer, nullable=False)
    revenue = Column(DECIMAL(20, 2))
    eps = Column(DECIMAL(10, 4))
    earnings_date = Column(Date, index=True)
    beat_expectations = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())
