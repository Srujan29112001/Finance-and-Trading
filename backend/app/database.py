"""
Database Connections and Initialization
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from pymongo import MongoClient
from pymongo.database import Database
from qdrant_client import QdrantClient
from neo4j import GraphDatabase, AsyncGraphDatabase
from redis import asyncio as aioredis
from loguru import logger
from typing import AsyncGenerator
import asyncpg

from app.config import settings

# SQLAlchemy Base
Base = declarative_base()

# Database connections
postgres_engine = None
async_session_maker = None
mongodb_client = None
mongodb_db = None
qdrant_client = None
neo4j_driver = None
redis_client = None


async def init_db():
    """Initialize all database connections."""
    global postgres_engine, async_session_maker, mongodb_client, mongodb_db
    global qdrant_client, neo4j_driver, redis_client

    try:
        # PostgreSQL (using asyncpg for async support)
        DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        postgres_engine = create_async_engine(
            DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20
        )
        async_session_maker = async_sessionmaker(
            postgres_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("✓ PostgreSQL connection initialized")

        # MongoDB
        mongodb_client = MongoClient(settings.MONGODB_URI)
        mongodb_db = mongodb_client[settings.MONGODB_DB]
        # Test connection
        mongodb_client.admin.command('ping')
        logger.info("✓ MongoDB connection initialized")

        # Qdrant Vector DB
        qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        # Ensure collection exists
        try:
            qdrant_client.get_collection(settings.QDRANT_COLLECTION)
        except Exception:
            from qdrant_client.models import Distance, VectorParams
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        logger.info("✓ Qdrant Vector DB connection initialized")

        # Neo4j Graph DB
        neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        # Test connection
        await neo4j_driver.verify_connectivity()
        logger.info("✓ Neo4j Graph DB connection initialized")

        # Redis
        redis_client = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✓ Redis connection initialized")

    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
        raise


async def close_db():
    """Close all database connections."""
    global postgres_engine, mongodb_client, qdrant_client, neo4j_driver, redis_client

    try:
        if postgres_engine:
            await postgres_engine.dispose()
            logger.info("PostgreSQL connection closed")

        if mongodb_client:
            mongodb_client.close()
            logger.info("MongoDB connection closed")

        if qdrant_client:
            qdrant_client.close()
            logger.info("Qdrant connection closed")

        if neo4j_driver:
            await neo4j_driver.close()
            logger.info("Neo4j connection closed")

        if redis_client:
            await redis_client.close()
            logger.info("Redis connection closed")

    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_mongodb() -> Database:
    """Get MongoDB database instance."""
    return mongodb_db


def get_qdrant() -> QdrantClient:
    """Get Qdrant client instance."""
    return qdrant_client


def get_neo4j():
    """Get Neo4j driver instance."""
    return neo4j_driver


async def get_redis():
    """Get Redis client instance."""
    return redis_client


# Health check functions
async def check_postgres_health() -> bool:
    """Check PostgreSQL connection health."""
    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False


async def check_mongodb_health() -> bool:
    """Check MongoDB connection health."""
    try:
        mongodb_client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return False


async def check_qdrant_health() -> bool:
    """Check Qdrant connection health."""
    try:
        qdrant_client.get_collections()
        return True
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return False


async def check_neo4j_health() -> bool:
    """Check Neo4j connection health."""
    try:
        await neo4j_driver.verify_connectivity()
        return True
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        return False


async def check_redis_health() -> bool:
    """Check Redis connection health."""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def get_all_health_status() -> dict:
    """Get health status of all database connections."""
    return {
        "postgres": await check_postgres_health(),
        "mongodb": await check_mongodb_health(),
        "qdrant": await check_qdrant_health(),
        "neo4j": await check_neo4j_health(),
        "redis": await check_redis_health()
    }
