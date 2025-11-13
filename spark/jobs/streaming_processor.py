"""
Apache Spark Structured Streaming Job
Processes real-time market data, news, and social media from Kafka
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
POSTGRES_JDBC_URL = "jdbc:postgresql://postgres:5432/financedb"
POSTGRES_PROPERTIES = {
    "user": "financeuser",
    "password": "financepass",
    "driver": "org.postgresql.Driver"
}


def create_spark_session():
    """Create Spark session with necessary configurations."""
    return SparkSession.builder \
        .appName("FinanceAnalyticsStreaming") \
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.postgresql:postgresql:42.6.0") \
        .config("spark.sql.streaming.checkpointLocation", "/opt/spark-data/checkpoints") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()


def process_price_stream(spark):
    """Process market price data stream."""
    logger.info("Starting price stream processing...")

    # Define schema for price data
    price_schema = StructType([
        StructField("symbol", StringType()),
        StructField("timestamp", StringType()),
        StructField("open", DoubleType()),
        StructField("high", DoubleType()),
        StructField("low", DoubleType()),
        StructField("close", DoubleType()),
        StructField("volume", LongType()),
        StructField("vwap", DoubleType())
    ])

    # Read from Kafka
    price_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "market_prices") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON
    price_data = price_df \
        .select(from_json(col("value").cast("string"), price_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp")))

    # Calculate rolling averages (windowed aggregations)
    windowed_avg = price_data \
        .withWatermark("timestamp", "1 minute") \
        .groupBy(
            col("symbol"),
            window(col("timestamp"), "5 minutes", "1 minute")
        ) \
        .agg(
            avg("close").alias("avg_price_5m"),
            sum("volume").alias("total_volume_5m"),
            max("high").alias("max_high_5m"),
            min("low").alias("min_low_5m"),
            count("*").alias("tick_count")
        )

    # Detect anomalies (volume spikes)
    anomalies = windowed_avg \
        .filter(col("total_volume_5m") > 1000000) \
        .withColumn("alert_type", lit("VOLUME_SPIKE")) \
        .withColumn("severity", lit("MEDIUM")) \
        .withColumn("message",
                    concat(lit("High volume detected for "), col("symbol"),
                           lit(": "), col("total_volume_5m").cast("string")))

    # Write price data to PostgreSQL
    price_query = price_data \
        .writeStream \
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "stock_prices", "append"
        )) \
        .outputMode("append") \
        .start()

    # Write anomalies
    anomaly_query = anomalies \
        .writeStream \
        .foreachBatch(lambda batch_df, batch_id: write_alerts_to_postgres(batch_df, batch_id)) \
        .outputMode("complete") \
        .start()

    return [price_query, anomaly_query]


def process_news_stream(spark):
    """Process news events stream."""
    logger.info("Starting news stream processing...")

    news_schema = StructType([
        StructField("symbol", StringType()),
        StructField("source", StringType()),
        StructField("headline", StringType()),
        StructField("url", StringType()),
        StructField("published_at", StringType()),
        StructField("sentiment", DoubleType()),
        StructField("summary", StringType())
    ])

    news_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "news_events") \
        .option("startingOffsets", "latest") \
        .load()

    news_data = news_df \
        .select(from_json(col("value").cast("string"), news_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("published_at"))) \
        .withColumn("sentiment_label",
                    when(col("sentiment") > 0.1, "positive")
                    .when(col("sentiment") < -0.1, "negative")
                    .otherwise("neutral"))

    # Write sentiment scores to PostgreSQL
    sentiment_query = news_data \
        .select(
            col("symbol"),
            lit("news").alias("source"),
            col("sentiment").alias("sentiment_score"),
            col("sentiment_label"),
            col("headline").alias("text_sample"),
            col("timestamp")
        ) \
        .writeStream \
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "sentiment_scores", "append"
        )) \
        .outputMode("append") \
        .start()

    return [sentiment_query]


def process_social_stream(spark):
    """Process social media stream."""
    logger.info("Starting social media stream processing...")

    social_schema = StructType([
        StructField("symbol", StringType()),
        StructField("source", StringType()),
        StructField("user", StringType()),
        StructField("text", StringType()),
        StructField("sentiment", DoubleType()),
        StructField("likes", IntegerType()),
        StructField("retweets", IntegerType()),
        StructField("timestamp", StringType())
    ])

    social_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", "social_tweets") \
        .option("startingOffsets", "latest") \
        .load()

    social_data = social_df \
        .select(from_json(col("value").cast("string"), social_schema).alias("data")) \
        .select("data.*") \
        .withColumn("timestamp", to_timestamp(col("timestamp"))) \
        .withColumn("sentiment_label",
                    when(col("sentiment") > 0.1, "positive")
                    .when(col("sentiment") < -0.1, "negative")
                    .otherwise("neutral"))

    # Write sentiment to PostgreSQL
    sentiment_query = social_data \
        .select(
            col("symbol"),
            col("source"),
            col("sentiment").alias("sentiment_score"),
            col("sentiment_label"),
            col("text").alias("text_sample"),
            col("timestamp")
        ) \
        .writeStream \
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "sentiment_scores", "append"
        )) \
        .outputMode("append") \
        .start()

    return [sentiment_query]


def write_to_postgres(batch_df, table_name, mode="append"):
    """Write batch DataFrame to PostgreSQL."""
    try:
        if batch_df.count() > 0:
            batch_df.write \
                .jdbc(
                    url=POSTGRES_JDBC_URL,
                    table=table_name,
                    mode=mode,
                    properties=POSTGRES_PROPERTIES
                )
            logger.info(f"✓ Wrote {batch_df.count()} records to {table_name}")
    except Exception as e:
        logger.error(f"Error writing to PostgreSQL: {e}")


def write_alerts_to_postgres(batch_df, batch_id):
    """Write alerts to PostgreSQL."""
    try:
        if batch_df.count() > 0:
            # Transform for alerts table
            alerts_df = batch_df.select(
                col("symbol"),
                col("alert_type"),
                col("severity"),
                col("message"),
                current_timestamp().alias("timestamp")
            )

            write_to_postgres(alerts_df, "market_alerts", "append")
    except Exception as e:
        logger.error(f"Error writing alerts: {e}")


def main():
    """Main function to start all streaming jobs."""
    logger.info("=" * 60)
    logger.info("Finance Analytics Spark Streaming Starting...")
    logger.info("=" * 60)

    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    logger.info("✓ Spark session created")

    # Start all streaming queries
    queries = []

    try:
        queries.extend(process_price_stream(spark))
        queries.extend(process_news_stream(spark))
        queries.extend(process_social_stream(spark))

        logger.info(f"✓ Started {len(queries)} streaming queries")

        # Wait for all queries
        for query in queries:
            query.awaitTermination()

    except KeyboardInterrupt:
        logger.info("Stopping streaming queries...")
        for query in queries:
            query.stop()
        spark.stop()


if __name__ == "__main__":
    main()
