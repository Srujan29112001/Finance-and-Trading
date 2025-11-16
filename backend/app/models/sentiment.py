"""Sentiment Models"""

from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=True, index=True)
    headline = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    url = Column(String(500), nullable=True)
    sentiment = Column(DECIMAL(5, 4), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    sentiment_score = Column(DECIMAL(5, 4), nullable=False)
    sentiment_label = Column(String(20))
    text_sample = Column(Text)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    news_count = Column(Integer, default=0)
    social_count = Column(Integer, default=0)
    score = Column(DECIMAL(5, 4), nullable=True)
    label = Column(String(20), nullable=True)
