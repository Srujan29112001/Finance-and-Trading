-- Finance Analytics Database Schema

-- Stock price data (time-series)
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4),
    volume BIGINT,
    vwap DECIMAL(12, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_timestamp ON stock_prices(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_timestamp ON stock_prices(timestamp DESC);

-- Technical indicators
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    sma_20 DECIMAL(12, 4),
    sma_50 DECIMAL(12, 4),
    ema_12 DECIMAL(12, 4),
    ema_26 DECIMAL(12, 4),
    rsi_14 DECIMAL(8, 4),
    macd DECIMAL(12, 4),
    macd_signal DECIMAL(12, 4),
    bollinger_upper DECIMAL(12, 4),
    bollinger_middle DECIMAL(12, 4),
    bollinger_lower DECIMAL(12, 4),
    atr_14 DECIMAL(12, 4),
    obv BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date ON technical_indicators(symbol, date DESC);

-- Market anomalies and alerts
CREATE TABLE IF NOT EXISTS market_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    message TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_alerts_symbol ON market_alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_market_alerts_timestamp ON market_alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_alerts_severity ON market_alerts(severity);

-- Trading signals from RL agent
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- 'BUY', 'SELL', 'HOLD'
    confidence DECIMAL(5, 4) NOT NULL,
    price DECIMAL(12, 4) NOT NULL,
    target_price DECIMAL(12, 4),
    stop_loss DECIMAL(12, 4),
    reasoning TEXT,
    metadata JSONB,
    timestamp TIMESTAMP NOT NULL,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol ON trading_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_signals_timestamp ON trading_signals(timestamp DESC);

-- Sentiment scores
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'news', 'twitter', 'reddit'
    sentiment_score DECIMAL(5, 4) NOT NULL, -- -1.0 to 1.0
    sentiment_label VARCHAR(20), -- 'positive', 'negative', 'neutral'
    text_sample TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sentiment_scores_symbol_timestamp ON sentiment_scores(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_scores_source ON sentiment_scores(source);

-- Earnings reports
CREATE TABLE IF NOT EXISTS earnings_reports (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    quarter VARCHAR(10) NOT NULL,
    year INT NOT NULL,
    revenue DECIMAL(20, 2),
    eps DECIMAL(10, 4),
    earnings_date DATE,
    beat_expectations BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, quarter, year)
);

CREATE INDEX IF NOT EXISTS idx_earnings_reports_symbol ON earnings_reports(symbol);
CREATE INDEX IF NOT EXISTS idx_earnings_reports_date ON earnings_reports(earnings_date DESC);

-- User portfolio (for tracking)
CREATE TABLE IF NOT EXISTS user_portfolios (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    avg_purchase_price DECIMAL(12, 4) NOT NULL,
    current_value DECIMAL(20, 2),
    profit_loss DECIMAL(20, 2),
    profit_loss_pct DECIMAL(8, 4),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_user_portfolios_user_id ON user_portfolios(user_id);

-- Trading history
CREATE TABLE IF NOT EXISTS trading_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL, -- 'BUY', 'SELL'
    quantity DECIMAL(18, 8) NOT NULL,
    price DECIMAL(12, 4) NOT NULL,
    total_value DECIMAL(20, 2) NOT NULL,
    fees DECIMAL(12, 4),
    timestamp TIMESTAMP NOT NULL,
    strategy VARCHAR(50), -- 'manual', 'rl_agent', 'copilot_suggestion'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trading_history_user_id ON trading_history(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_history_symbol ON trading_history(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_history_timestamp ON trading_history(timestamp DESC);

-- Risk metrics
CREATE TABLE IF NOT EXISTS risk_metrics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    portfolio_value DECIMAL(20, 2),
    var_95 DECIMAL(20, 2), -- Value at Risk 95%
    var_99 DECIMAL(20, 2), -- Value at Risk 99%
    sharpe_ratio DECIMAL(8, 4),
    sortino_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    beta DECIMAL(8, 4),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_metrics_user_id_timestamp ON risk_metrics(user_id, timestamp DESC);

-- Behavioral analytics (computational psychiatry aspect)
CREATE TABLE IF NOT EXISTS user_behavior_analytics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    behavior_type VARCHAR(50) NOT NULL, -- 'impulsive_trading', 'loss_chasing', 'profit_taking', etc.
    risk_score DECIMAL(5, 4), -- 0.0 to 1.0
    trade_frequency_1h INT,
    avg_trade_size DECIMAL(20, 2),
    emotional_state VARCHAR(20), -- 'calm', 'anxious', 'greedy', 'fearful'
    recommendation TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_behavior_user_id ON user_behavior_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_behavior_timestamp ON user_behavior_analytics(timestamp DESC);

-- LLM conversation history
CREATE TABLE IF NOT EXISTS llm_conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(50),
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    context_used JSONB,
    tools_used TEXT[],
    response_time_ms INT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_conversations_session_id ON llm_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_conversations_timestamp ON llm_conversations(timestamp DESC);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(12, 6),
    evaluation_date DATE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_performance_model ON model_performance(model_name, model_version);
CREATE INDEX IF NOT EXISTS idx_model_performance_date ON model_performance(evaluation_date DESC);

-- Create materialized view for latest prices
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_stock_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    vwap
FROM stock_prices
ORDER BY symbol, timestamp DESC;

CREATE UNIQUE INDEX ON latest_stock_prices(symbol);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_latest_prices()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY latest_stock_prices;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aggregated market statistics view
CREATE OR REPLACE VIEW market_statistics AS
SELECT
    symbol,
    DATE(timestamp) as date,
    MIN(low) as day_low,
    MAX(high) as day_high,
    AVG(close) as avg_price,
    SUM(volume) as total_volume,
    COUNT(*) as num_ticks
FROM stock_prices
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY symbol, DATE(timestamp)
ORDER BY date DESC, symbol;

-- Insert some initial test data for development
INSERT INTO stock_prices (symbol, timestamp, open, high, low, close, volume, vwap)
VALUES
    ('AAPL', NOW() - INTERVAL '1 hour', 175.20, 175.80, 175.00, 175.50, 1000000, 175.40),
    ('TSLA', NOW() - INTERVAL '1 hour', 250.00, 252.00, 249.50, 251.50, 800000, 251.00),
    ('GOOGL', NOW() - INTERVAL '1 hour', 140.50, 141.20, 140.30, 141.00, 500000, 140.80),
    ('MSFT', NOW() - INTERVAL '1 hour', 380.00, 381.50, 379.80, 381.00, 600000, 380.50),
    ('AMZN', NOW() - INTERVAL '1 hour', 145.00, 145.80, 144.70, 145.50, 700000, 145.30)
ON CONFLICT (symbol, timestamp) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO financeuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO financeuser;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO financeuser;
