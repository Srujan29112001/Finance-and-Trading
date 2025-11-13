"""
Data Producers for Finance Analytics Platform
Simulates real-time market data, news, and social media feeds
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
import sys
import os

from kafka import KafkaProducer
from kafka.errors import KafkaError


# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPICS = {
    "prices": "market_prices",
    "news": "news_events",
    "tweets": "social_tweets",
}

# Stock symbols to simulate
SYMBOLS = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "NFLX"]

# News templates
NEWS_TEMPLATES = [
    "{company} announces record Q{quarter} earnings, beating analyst expectations",
    "{company} stock surges on positive guidance for upcoming quarter",
    "Analysts upgrade {company} rating to 'Strong Buy'",
    "{company} faces regulatory challenges in new market",
    "{company} CEO announces major restructuring plan",
    "Breaking: {company} reveals new product line at annual conference",
    "{company} reports disappointing earnings, shares tumble",
    "Market reacts to {company}'s latest partnership announcement",
    "{company} announces $1B stock buyback program",
    "Insider trading alert: {company} executives sell shares"
]

# Social media templates
TWEET_TEMPLATES = [
    "Just bought more ${symbol}! 🚀 This stock is going to the moon!",
    "${symbol} looking bearish today. Time to sell?",
    "Why is ${symbol} mooning? What news did I miss?",
    "${symbol} is the future! Great company, great stock!",
    "Sold all my ${symbol}. Taking profits before it drops.",
    "Should I buy ${symbol} at this price? Thoughts?",
    "${symbol} breaking out! Next stop: all-time highs!",
    "Technical analysis shows ${symbol} hitting resistance...",
    "Fundamentals look strong for ${symbol}. Long term hold.",
    "Market overreacting to ${symbol} news. Great buying opportunity!"
]

COMPANY_NAMES = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "GOOGL": "Google",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "META": "Meta",
    "NFLX": "Netflix"
}


class MarketDataProducer:
    """Producer for simulated market price data."""

    def __init__(self, producer: KafkaProducer):
        self.producer = producer
        self.topic = KAFKA_TOPICS["prices"]
        # Initialize base prices
        self.prices = {symbol: random.uniform(100, 500) for symbol in SYMBOLS}
        logger.info(f"✓ Market Data Producer initialized")

    def generate_tick(self, symbol: str) -> Dict[str, Any]:
        """Generate a price tick for a symbol."""
        # Simulate price movement (random walk with small steps)
        change_pct = random.uniform(-0.02, 0.02)  # -2% to +2%
        self.prices[symbol] *= (1 + change_pct)

        price = self.prices[symbol]
        volume = random.randint(10000, 500000)

        # Simulate OHLC for 1-minute bar
        open_price = price * random.uniform(0.998, 1.002)
        high = max(price, open_price) * random.uniform(1.0, 1.005)
        low = min(price, open_price) * random.uniform(0.995, 1.0)
        close = price
        vwap = (high + low + close) / 3

        tick = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": volume,
            "vwap": round(vwap, 2)
        }

        return tick

    def produce(self):
        """Continuously produce market data."""
        logger.info(f"Starting market data production to topic: {self.topic}")

        while True:
            try:
                for symbol in SYMBOLS:
                    tick = self.generate_tick(symbol)

                    # Send to Kafka
                    self.producer.send(
                        self.topic,
                        key=symbol.encode('utf-8'),
                        value=json.dumps(tick).encode('utf-8')
                    )

                    logger.debug(f"Produced price tick: {symbol} @ ${tick['close']}")

                # Produce ticks every 5 seconds
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error producing market data: {e}")
                time.sleep(1)


class NewsProducer:
    """Producer for simulated news events."""

    def __init__(self, producer: KafkaProducer):
        self.producer = producer
        self.topic = KAFKA_TOPICS["news"]
        logger.info(f"✓ News Producer initialized")

    def generate_news(self) -> Dict[str, Any]:
        """Generate a news article."""
        symbol = random.choice(SYMBOLS)
        company = COMPANY_NAMES[symbol]
        template = random.choice(NEWS_TEMPLATES)

        headline = template.format(
            company=company,
            quarter=random.choice(["1", "2", "3", "4"])
        )

        # Simulate sentiment
        sentiment = random.uniform(-1.0, 1.0)
        if "record" in headline or "surge" in headline or "upgrade" in headline:
            sentiment = random.uniform(0.5, 1.0)
        elif "disappointing" in headline or "tumble" in headline or "challenges" in headline:
            sentiment = random.uniform(-1.0, -0.5)

        news = {
            "symbol": symbol,
            "source": random.choice(["Reuters", "Bloomberg", "CNBC", "Wall Street Journal", "Financial Times"]),
            "headline": headline,
            "url": f"https://news.example.com/{symbol.lower()}-{int(time.time())}",
            "published_at": datetime.utcnow().isoformat(),
            "sentiment": round(sentiment, 3),
            "summary": f"Full article about {headline.lower()}..."
        }

        return news

    def produce(self):
        """Continuously produce news events."""
        logger.info(f"Starting news production to topic: {self.topic}")

        while True:
            try:
                news = self.generate_news()

                # Send to Kafka
                self.producer.send(
                    self.topic,
                    key=news["symbol"].encode('utf-8'),
                    value=json.dumps(news).encode('utf-8')
                )

                logger.info(f"Produced news: {news['headline'][:60]}...")

                # Produce news every 30-60 seconds
                time.sleep(random.uniform(30, 60))

            except Exception as e:
                logger.error(f"Error producing news: {e}")
                time.sleep(1)


class SocialMediaProducer:
    """Producer for simulated social media posts (tweets, reddit, etc)."""

    def __init__(self, producer: KafkaProducer):
        self.producer = producer
        self.topic = KAFKA_TOPICS["tweets"]
        logger.info(f"✓ Social Media Producer initialized")

    def generate_tweet(self) -> Dict[str, Any]:
        """Generate a social media post."""
        symbol = random.choice(SYMBOLS)
        template = random.choice(TWEET_TEMPLATES)
        text = template.format(symbol=symbol)

        # Determine sentiment from text
        bullish_words = ["buy", "moon", "surge", "breakout", "strong", "great", "opportunity"]
        bearish_words = ["sell", "drop", "bearish", "resistance", "disappointing"]

        text_lower = text.lower()
        sentiment = 0.0

        for word in bullish_words:
            if word in text_lower:
                sentiment += 0.3

        for word in bearish_words:
            if word in text_lower:
                sentiment -= 0.3

        sentiment = max(-1.0, min(1.0, sentiment))  # Clamp to [-1, 1]

        tweet = {
            "symbol": symbol,
            "source": random.choice(["twitter", "reddit", "stocktwits"]),
            "user": f"user_{random.randint(1000, 9999)}",
            "text": text,
            "sentiment": round(sentiment, 3),
            "likes": random.randint(0, 1000),
            "retweets": random.randint(0, 500),
            "timestamp": datetime.utcnow().isoformat()
        }

        return tweet

    def produce(self):
        """Continuously produce social media posts."""
        logger.info(f"Starting social media production to topic: {self.topic}")

        while True:
            try:
                tweet = self.generate_tweet()

                # Send to Kafka
                self.producer.send(
                    self.topic,
                    key=tweet["symbol"].encode('utf-8'),
                    value=json.dumps(tweet).encode('utf-8')
                )

                logger.debug(f"Produced tweet: {tweet['text'][:50]}...")

                # Produce tweets every 10-20 seconds
                time.sleep(random.uniform(10, 20))

            except Exception as e:
                logger.error(f"Error producing social media: {e}")
                time.sleep(1)


def create_kafka_producer() -> KafkaProducer:
    """Create and return Kafka producer with retries."""
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS} (attempt {attempt + 1}/{max_retries})...")

            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: v,
                key_serializer=lambda k: k,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )

            logger.info("✓ Connected to Kafka successfully")
            return producer

        except KafkaError as e:
            logger.warning(f"Failed to connect to Kafka: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not connect to Kafka.")
                raise


def main():
    """Main function to start all producers."""
    logger.info("=" * 60)
    logger.info("Finance Analytics Data Producers Starting...")
    logger.info("=" * 60)

    # Wait for Kafka to be ready
    time.sleep(10)

    # Create Kafka producer
    producer = create_kafka_producer()

    # Create producer instances
    market_producer = MarketDataProducer(producer)
    news_producer = NewsProducer(producer)
    social_producer = SocialMediaProducer(producer)

    # Start producers in separate threads
    import threading

    threads = [
        threading.Thread(target=market_producer.produce, daemon=True),
        threading.Thread(target=news_producer.produce, daemon=True),
        threading.Thread(target=social_producer.produce, daemon=True)
    ]

    for thread in threads:
        thread.start()

    logger.info("✓ All producers started successfully")
    logger.info(f"✓ Producing data for symbols: {', '.join(SYMBOLS)}")

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
            logger.info("Producers running... (heartbeat)")
    except KeyboardInterrupt:
        logger.info("Shutting down producers...")
        producer.close()


if __name__ == "__main__":
    main()
