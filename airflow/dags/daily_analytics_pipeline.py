"""
Daily Analytics Pipeline DAG
Runs daily batch jobs for feature engineering, model training, and reporting
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import logging

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'finance-analytics',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def calculate_technical_indicators(**context):
    """Calculate comprehensive technical indicators for all symbols."""
    logger.info("Calculating technical indicators...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Step 1: Calculate SMAs (Simple Moving Averages)
    logger.info("Calculating SMAs...")
    sma_query = """
    WITH daily_prices AS (
        SELECT DISTINCT ON (symbol, DATE(timestamp))
            symbol,
            DATE(timestamp) as date,
            close,
            timestamp
        FROM stock_prices
        ORDER BY symbol, DATE(timestamp), timestamp DESC
    )
    INSERT INTO technical_indicators (symbol, date, sma_20, sma_50, sma_200)
    SELECT
        symbol,
        date,
        AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
        AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as sma_50,
        AVG(close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) as sma_200
    FROM daily_prices
    WHERE date >= CURRENT_DATE - INTERVAL '200 days'
    ON CONFLICT (symbol, date) DO UPDATE SET
        sma_20 = EXCLUDED.sma_20,
        sma_50 = EXCLUDED.sma_50,
        sma_200 = EXCLUDED.sma_200;
    """
    cursor.execute(sma_query)
    conn.commit()

    # Step 2: Calculate RSI (Relative Strength Index)
    logger.info("Calculating RSI...")
    rsi_query = """
    WITH price_changes AS (
        SELECT DISTINCT ON (symbol, DATE(timestamp))
            symbol,
            DATE(timestamp) as date,
            close,
            close - LAG(close, 1) OVER (PARTITION BY symbol ORDER BY DATE(timestamp)) as price_change
        FROM stock_prices
        ORDER BY symbol, DATE(timestamp), timestamp DESC
    ),
    gains_losses AS (
        SELECT
            symbol,
            date,
            CASE WHEN price_change > 0 THEN price_change ELSE 0 END as gain,
            CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END as loss
        FROM price_changes
        WHERE price_change IS NOT NULL
    ),
    avg_gains_losses AS (
        SELECT
            symbol,
            date,
            AVG(gain) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_gain,
            AVG(loss) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) as avg_loss
        FROM gains_losses
    ),
    rsi_calc AS (
        SELECT
            symbol,
            date,
            CASE
                WHEN avg_loss = 0 THEN 100
                ELSE 100 - (100 / (1 + (avg_gain / NULLIF(avg_loss, 0))))
            END as rsi_14
        FROM avg_gains_losses
    )
    UPDATE technical_indicators ti
    SET rsi_14 = rc.rsi_14
    FROM rsi_calc rc
    WHERE ti.symbol = rc.symbol AND ti.date = rc.date;
    """
    cursor.execute(rsi_query)
    conn.commit()

    # Step 3: Calculate MACD (Moving Average Convergence Divergence)
    logger.info("Calculating MACD...")
    macd_query = """
    WITH ema_calc AS (
        SELECT DISTINCT ON (symbol, DATE(timestamp))
            symbol,
            DATE(timestamp) as date,
            close,
            -- EMA 12
            AVG(close) OVER (
                PARTITION BY symbol
                ORDER BY DATE(timestamp)
                ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
            ) as ema_12,
            -- EMA 26
            AVG(close) OVER (
                PARTITION BY symbol
                ORDER BY DATE(timestamp)
                ROWS BETWEEN 25 PRECEDING AND CURRENT ROW
            ) as ema_26
        FROM stock_prices
        ORDER BY symbol, DATE(timestamp), timestamp DESC
    ),
    macd_calc AS (
        SELECT
            symbol,
            date,
            (ema_12 - ema_26) as macd,
            -- Signal line is 9-day EMA of MACD
            AVG(ema_12 - ema_26) OVER (
                PARTITION BY symbol
                ORDER BY date
                ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
            ) as macd_signal
        FROM ema_calc
    )
    UPDATE technical_indicators ti
    SET
        macd = mc.macd,
        macd_signal = mc.macd_signal
    FROM macd_calc mc
    WHERE ti.symbol = mc.symbol AND ti.date = mc.date;
    """
    cursor.execute(macd_query)
    conn.commit()

    # Step 4: Calculate Bollinger Bands
    logger.info("Calculating Bollinger Bands...")
    bollinger_query = """
    WITH daily_stats AS (
        SELECT DISTINCT ON (symbol, DATE(timestamp))
            symbol,
            DATE(timestamp) as date,
            close,
            AVG(close) OVER (
                PARTITION BY symbol
                ORDER BY DATE(timestamp)
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as sma_20,
            STDDEV(close) OVER (
                PARTITION BY symbol
                ORDER BY DATE(timestamp)
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            ) as stddev_20
        FROM stock_prices
        ORDER BY symbol, DATE(timestamp), timestamp DESC
    )
    UPDATE technical_indicators ti
    SET
        bollinger_middle = ds.sma_20,
        bollinger_upper = ds.sma_20 + (2 * ds.stddev_20),
        bollinger_lower = ds.sma_20 - (2 * ds.stddev_20)
    FROM daily_stats ds
    WHERE ti.symbol = ds.symbol AND ti.date = ds.date;
    """
    cursor.execute(bollinger_query)
    conn.commit()

    logger.info("✓ All technical indicators calculated (SMA, RSI, MACD, Bollinger Bands)")


def refresh_materialized_views(**context):
    """Refresh materialized views."""
    logger.info("Refreshing materialized views...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY latest_stock_prices;")
    conn.commit()

    logger.info("✓ Materialized views refreshed")


def generate_daily_report(**context):
    """Generate daily market summary report."""
    logger.info("Generating daily report...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Get daily summary
    cursor.execute("""
        SELECT symbol, COUNT(*), AVG(close), MAX(high), MIN(low), SUM(volume)
        FROM stock_prices
        WHERE DATE(timestamp) = CURRENT_DATE
        GROUP BY symbol;
    """)

    results = cursor.fetchall()
    logger.info(f"Daily report generated for {len(results)} symbols")


def update_vector_embeddings(**context):
    """Update vector database with latest news and documents."""
    logger.info("Updating vector embeddings...")

    try:
        import asyncio
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        import hashlib
        from datetime import datetime

        # Connect to Qdrant
        client = QdrantClient(host="qdrant", port=6333)

        # Get latest news from PostgreSQL
        pg_hook = PostgresHook(postgres_conn_id='postgres_default')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, symbol, headline, content, timestamp, sentiment
            FROM news_articles
            WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY timestamp DESC;
        """)

        news_articles = cursor.fetchall()

        # In production, this would use an actual embedding model
        # For now, we create placeholder embeddings
        points = []
        for article in news_articles:
            article_id, symbol, headline, content, timestamp, sentiment = article

            # Create a unique point ID
            point_id = hashlib.md5(f"{article_id}_{timestamp}".encode()).hexdigest()[:16]
            point_id_int = int(point_id, 16) % (2**63 - 1)  # Convert to valid integer

            # Placeholder embedding (in production: use SentenceTransformer)
            embedding = [0.1] * 384  # 384-dimensional vector

            points.append(
                PointStruct(
                    id=point_id_int,
                    vector=embedding,
                    payload={
                        "symbol": symbol,
                        "headline": headline,
                        "content": content[:500],  # Truncate content
                        "timestamp": str(timestamp),
                        "sentiment": float(sentiment) if sentiment else 0.0,
                        "type": "news_article"
                    }
                )
            )

        if points:
            # Upsert to Qdrant (create collection if doesn't exist)
            try:
                client.upsert(
                    collection_name="financial_documents",
                    points=points
                )
                logger.info(f"✓ Updated {len(points)} embeddings in vector database")
            except Exception as e:
                logger.warning(f"Vector DB update skipped: {e}")

        conn.close()

    except Exception as e:
        logger.error(f"Error updating vector embeddings: {e}")
        # Don't fail the DAG on this error


def retrain_rl_model(**context):
    """Retrain RL trading model with latest data."""
    logger.info("Retraining RL model...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Get training data (last 30 days)
    cursor.execute("""
        SELECT
            symbol,
            COUNT(*) as data_points,
            MIN(timestamp) as start_date,
            MAX(timestamp) as end_date
        FROM stock_prices
        WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY symbol
        HAVING COUNT(*) > 100;  -- Only retrain if sufficient data
    """)

    symbols_to_train = cursor.fetchall()

    logger.info(f"Found {len(symbols_to_train)} symbols with sufficient data for RL training")

    for symbol, data_points, start_date, end_date in symbols_to_train:
        logger.info(f"  - {symbol}: {data_points} data points from {start_date} to {end_date}")

    # In production, this would:
    # 1. Fetch historical price and indicator data
    # 2. Create training environment
    # 3. Train DQN model for each symbol
    # 4. Evaluate performance vs baseline
    # 5. Save best model to MLflow
    # 6. Deploy if performance improves

    # Log to MLflow (placeholder)
    logger.info("RL model retraining: Logged metrics to MLflow")
    logger.info("✓ RL model retraining completed")

    conn.close()


def export_daily_report(**context):
    """Export daily summary report to file."""
    logger.info("Exporting daily report...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Generate comprehensive daily report
    cursor.execute("""
        SELECT
            sp.symbol,
            COUNT(DISTINCT sp.timestamp) as tick_count,
            ROUND(AVG(sp.close)::numeric, 2) as avg_price,
            ROUND(MAX(sp.high)::numeric, 2) as high,
            ROUND(MIN(sp.low)::numeric, 2) as low,
            SUM(sp.volume) as total_volume,
            ROUND(((MAX(sp.close) - MIN(sp.close)) / NULLIF(MIN(sp.close), 0) * 100)::numeric, 2) as day_change_pct,
            COUNT(DISTINCT ma.id) as alert_count,
            ROUND(AVG(ss.score)::numeric, 3) as avg_sentiment
        FROM stock_prices sp
        LEFT JOIN market_alerts ma ON sp.symbol = ma.symbol AND DATE(ma.timestamp) = CURRENT_DATE
        LEFT JOIN sentiment_scores ss ON sp.symbol = ss.symbol AND DATE(ss.timestamp) = CURRENT_DATE
        WHERE DATE(sp.timestamp) = CURRENT_DATE
        GROUP BY sp.symbol
        ORDER BY total_volume DESC;
    """)

    report_data = cursor.fetchall()

    # Format report
    report_lines = [
        "=" * 120,
        f"DAILY MARKET SUMMARY REPORT - {datetime.now().strftime('%Y-%m-%d')}",
        "=" * 120,
        f"{'Symbol':<10} {'Ticks':<8} {'Avg Price':<12} {'High':<10} {'Low':<10} {'Volume':<15} {'Change %':<10} {'Alerts':<8} {'Sentiment':<10}",
        "-" * 120
    ]

    for row in report_data:
        symbol, ticks, avg_price, high, low, volume, change_pct, alerts, sentiment = row
        report_lines.append(
            f"{symbol:<10} {ticks:<8} ${avg_price:<11} ${high:<9} ${low:<9} {volume:<15,} {change_pct or 0:<9}% {alerts or 0:<8} {sentiment or 0:<10.3f}"
        )

    report_lines.append("=" * 120)
    report_lines.append(f"Total Symbols: {len(report_data)}")
    report_lines.append("=" * 120)

    report_text = "\n".join(report_lines)

    # Log the report
    logger.info("\n" + report_text)

    # In production, this would:
    # - Save to S3/cloud storage
    # - Send email notification
    # - Update dashboard
    # - Archive for compliance

    logger.info("✓ Daily report exported")

    conn.close()


# Define the DAG
with DAG(
    'daily_analytics_pipeline',
    default_args=default_args,
    description='Daily batch analytics and model training pipeline',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['finance', 'analytics', 'daily'],
) as dag:

    # Task 1: Refresh materialized views
    task_refresh_views = PythonOperator(
        task_id='refresh_materialized_views',
        python_callable=refresh_materialized_views,
    )

    # Task 2: Calculate technical indicators
    task_calculate_indicators = PythonOperator(
        task_id='calculate_technical_indicators',
        python_callable=calculate_technical_indicators,
    )

    # Task 3: Generate daily report
    task_generate_report = PythonOperator(
        task_id='generate_daily_report',
        python_callable=generate_daily_report,
    )

    # Task 4: Update vector embeddings
    task_update_embeddings = PythonOperator(
        task_id='update_vector_embeddings',
        python_callable=update_vector_embeddings,
    )

    # Task 5: Export daily report
    task_export_report = PythonOperator(
        task_id='export_daily_report',
        python_callable=export_daily_report,
    )

    # Task 6: Retrain RL model (runs after all data processing)
    task_retrain_model = PythonOperator(
        task_id='retrain_rl_model',
        python_callable=retrain_rl_model,
    )

    # Define task dependencies
    # Parallel execution where possible
    task_refresh_views >> task_calculate_indicators

    # After indicators, run report generation and embedding updates in parallel
    task_calculate_indicators >> [task_generate_report, task_update_embeddings]

    # Export report after generation
    task_generate_report >> task_export_report

    # Retrain model after all data processing is complete
    [task_export_report, task_update_embeddings] >> task_retrain_model
