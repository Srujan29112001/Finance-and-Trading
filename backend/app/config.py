"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Settings
    API_TITLE: str = "Finance Analytics & Trading Co-Pilot API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000", "*"]

    # PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "financeuser")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "financepass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "financedb")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://financeuser:financepass@mongodb:27017/")
    MONGODB_DB: str = "financedb"

    # Qdrant Vector DB
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "financial_docs"

    # Neo4j Graph DB
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "financepass")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    KAFKA_TOPICS: dict = {
        "prices": "market_prices",
        "news": "news_events",
        "tweets": "social_tweets",
        "alerts": "market_alerts",
        "signals": "trading_signals"
    }

    # MLflow
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")

    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    LLM_MODEL: str = "gpt-3.5-turbo"  # Can be changed to local model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # RL Agent Settings
    RL_MODEL_PATH: str = "/models/rl_agent"
    RL_RETRAIN_INTERVAL: int = 86400  # 24 hours in seconds

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Cache Settings
    CACHE_TTL: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
