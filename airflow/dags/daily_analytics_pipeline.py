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
    """Calculate technical indicators for all symbols."""
    logger.info("Calculating technical indicators...")

    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = pg_hook.get_conn()
    cursor = conn.cursor()

    # Example: Calculate SMA_20 for each symbol
    query = """
    INSERT INTO technical_indicators (symbol, date, sma_20, sma_50)
    SELECT
        symbol,
        DATE(timestamp) as date,
        AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) as sma_20,
        AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) as sma_50
    FROM stock_prices
    WHERE DATE(timestamp) = CURRENT_DATE
    ON CONFLICT (symbol, date) DO UPDATE SET
        sma_20 = EXCLUDED.sma_20,
        sma_50 = EXCLUDED.sma_50;
    """

    cursor.execute(query)
    conn.commit()
    logger.info("✓ Technical indicators calculated")


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


def retrain_rl_model(**context):
    """Retrain RL trading model with latest data."""
    logger.info("Retraining RL model...")

    # In production, this would trigger RL agent training
    # For now, just log
    logger.info("RL model retraining scheduled (placeholder)")


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

    # Task 4: Retrain RL model (weekly)
    task_retrain_model = PythonOperator(
        task_id='retrain_rl_model',
        python_callable=retrain_rl_model,
    )

    # Define task dependencies
    task_refresh_views >> task_calculate_indicators >> task_generate_report
    task_generate_report >> task_retrain_model
