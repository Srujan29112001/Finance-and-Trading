"""
Finance Analytics & Trading Co-Pilot - Streamlit Dashboard
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os

# Configuration
API_BASE_URL = os.getenv("FASTAPI_URL", "http://fastapi:8000")

# Page configuration
st.set_page_config(
    page_title="Finance Analytics & Trading Co-Pilot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .alert-high {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    .alert-medium {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)


def get_market_data(symbol, limit=100):
    """Fetch market data from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/market/prices/{symbol}",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return None
    except Exception as e:
        st.error(f"Error fetching market data: {e}")
        return None


def get_latest_price(symbol):
    """Fetch latest price for a symbol."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/market/latest/{symbol}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def get_market_summary(symbol):
    """Fetch market summary."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/market/summary/{symbol}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def get_sentiment(symbol):
    """Fetch sentiment data."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/analysis/sentiment/aggregate/{symbol}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def get_trading_signals(symbol):
    """Fetch trading signals."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/trading/signals/{symbol}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def get_alerts(limit=20):
    """Fetch recent alerts."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/alerts/recent", params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        return []


def ask_copilot(question, symbol=None):
    """Ask the AI co-pilot a question."""
    try:
        payload = {
            "message": question,
            "symbol": symbol
        }
        response = requests.post(
            f"{API_BASE_URL}/api/chat/ask",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error communicating with AI: {e}")
        return None


def plot_price_chart(df, symbol):
    """Create an interactive price chart."""
    if df is None or df.empty:
        st.warning("No price data available")
        return

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    ))

    fig.update_layout(
        title=f"{symbol} Price Chart",
        yaxis_title="Price ($)",
        xaxis_title="Time",
        template="plotly_white",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_volume_chart(df):
    """Create volume bar chart."""
    if df is None or df.empty:
        return

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name="Volume",
        marker_color='lightblue'
    ))

    fig.update_layout(
        title="Trading Volume",
        yaxis_title="Volume",
        xaxis_title="Time",
        template="plotly_white",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    """Main dashboard function."""

    # Header
    st.markdown('<div class="main-header">📈 Finance Analytics & Trading Co-Pilot</div>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.title("⚙️ Settings")

    # Symbol selection
    symbols = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "NVDA", "META", "NFLX"]
    selected_symbol = st.sidebar.selectbox("Select Stock Symbol", symbols, index=0)

    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        time.sleep(30)
        st.rerun()

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Market Overview",
        "🤖 AI Co-Pilot",
        "📈 Trading Signals",
        "🚨 Alerts",
        "ℹ️ About"
    ])

    # Tab 1: Market Overview
    with tab1:
        st.header(f"Market Overview - {selected_symbol}")

        # Fetch data
        summary = get_market_summary(selected_symbol)
        sentiment = get_sentiment(selected_symbol)

        if summary:
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Current Price",
                    f"${summary['current_price']:.2f}",
                    f"{summary['change_pct']:.2f}%"
                )

            with col2:
                st.metric(
                    "24h High",
                    f"${summary['high_24h']:.2f}"
                )

            with col3:
                st.metric(
                    "24h Low",
                    f"${summary['low_24h']:.2f}"
                )

            with col4:
                st.metric(
                    "Volume",
                    f"{summary['volume']:,}"
                )

        # Sentiment
        if sentiment:
            st.subheader("📊 Market Sentiment")
            sentiment_col1, sentiment_col2 = st.columns(2)

            with sentiment_col1:
                sentiment_score = sentiment.get('avg_sentiment', 0)
                sentiment_label = sentiment.get('sentiment_label', 'neutral')

                # Color code sentiment
                if sentiment_label == 'positive':
                    sentiment_color = 'green'
                elif sentiment_label == 'negative':
                    sentiment_color = 'red'
                else:
                    sentiment_color = 'gray'

                st.markdown(f"### Sentiment: <span style='color:{sentiment_color}'>{sentiment_label.upper()}</span>", unsafe_allow_html=True)
                st.metric("Sentiment Score", f"{sentiment_score:.3f}", help="Range: -1.0 (very negative) to +1.0 (very positive)")

            with sentiment_col2:
                st.metric("Data Points", sentiment.get('sample_size', 0))
                st.metric("Period", f"{sentiment.get('period_hours', 24)} hours")

        # Charts
        st.subheader("📈 Price Chart")
        price_data = get_market_data(selected_symbol, limit=100)

        if price_data is not None and not price_data.empty:
            plot_price_chart(price_data, selected_symbol)
            plot_volume_chart(price_data)
        else:
            st.info("Waiting for market data...")

    # Tab 2: AI Co-Pilot
    with tab2:
        st.header("🤖 AI Trading Co-Pilot")

        st.markdown("""
        Ask the AI Co-Pilot questions about the market, stocks, or get trading insights.

        **Example questions:**
        - Why did {symbol} spike today?
        - What's the sentiment on {symbol}?
        - Should I buy {symbol} now?
        - Summarize recent news for {symbol}
        """.format(symbol=selected_symbol))

        # Chat interface
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Display chat history
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**AI:** {message['content']}")
                if 'tools_used' in message and message['tools_used']:
                    with st.expander("🔧 Tools Used"):
                        st.write(", ".join(message['tools_used']))

        # Input
        user_question = st.text_input("Ask a question:", key="copilot_input")

        if st.button("Ask AI") and user_question:
            with st.spinner("AI is thinking..."):
                # Add user message
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_question
                })

                # Get AI response
                response = ask_copilot(user_question, selected_symbol)

                if response:
                    # Add AI response
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response['response'],
                        'tools_used': response.get('tools_used', [])
                    })

                    st.rerun()
                else:
                    st.error("Failed to get response from AI")

        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Tab 3: Trading Signals
    with tab3:
        st.header("📈 AI Trading Signals (RL Agent)")

        signals = get_trading_signals(selected_symbol)

        if signals and len(signals) > 0:
            latest_signal = signals[0]

            # Display latest signal
            st.subheader(f"Latest Signal for {selected_symbol}")

            signal_col1, signal_col2, signal_col3 = st.columns(3)

            with signal_col1:
                signal_type = latest_signal['signal_type']
                if signal_type == 'BUY':
                    st.success(f"🟢 {signal_type}")
                elif signal_type == 'SELL':
                    st.error(f"🔴 {signal_type}")
                else:
                    st.info(f"⚪ {signal_type}")

            with signal_col2:
                confidence = latest_signal['confidence']
                st.metric("Confidence", f"{confidence:.1%}")

            with signal_col3:
                st.metric("Price", f"${latest_signal['price']:.2f}")

            # Details
            st.markdown("**Reasoning:**")
            st.info(latest_signal.get('reasoning', 'No reasoning provided'))

            if latest_signal.get('target_price'):
                st.metric("Target Price", f"${latest_signal['target_price']:.2f}")

            if latest_signal.get('stop_loss'):
                st.metric("Stop Loss", f"${latest_signal['stop_loss']:.2f}")

            st.caption(f"Generated: {latest_signal['timestamp']}")

            # Historical signals
            st.subheader("Signal History")
            signals_df = pd.DataFrame(signals)
            st.dataframe(signals_df[['timestamp', 'signal_type', 'confidence', 'price']], use_container_width=True)

        else:
            st.info("No trading signals available yet. The RL agent may need to generate signals.")

            if st.button("Generate Signal Now"):
                with st.spinner("Generating trading signal..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/api/trading/signal/generate",
                            params={"symbol": selected_symbol},
                            timeout=30
                        )
                        if response.status_code == 200:
                            st.success("Signal generated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to generate signal")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Tab 4: Alerts
    with tab4:
        st.header("🚨 Market Alerts")

        alerts = get_alerts(limit=50)

        if alerts:
            for alert in alerts:
                severity = alert['severity'].lower()
                alert_class = f"alert-{severity}"

                st.markdown(f"""
                <div class="alert-box {alert_class}">
                    <strong>{alert['symbol']}</strong> - {alert['alert_type']}<br>
                    {alert['message']}<br>
                    <small>{alert['timestamp']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No alerts at this time")

    # Tab 5: About
    with tab5:
        st.header("ℹ️ About Finance Analytics & Trading Co-Pilot")

        st.markdown("""
        ## System Overview

        This platform combines cutting-edge technologies for real-time finance analytics and AI-powered trading assistance:

        ### 🏗️ Architecture

        - **Data Ingestion**: Apache Kafka for high-throughput streaming
        - **Stream Processing**: Apache Spark for real-time analytics
        - **Storage**: PostgreSQL, MongoDB, Neo4j, Qdrant Vector DB
        - **AI/ML**: LangChain with RAG/GraphRAG, Reinforcement Learning (DQN)
        - **API**: FastAPI with REST and GraphQL endpoints
        - **Monitoring**: Prometheus & Grafana

        ### 🤖 AI Capabilities

        - **RAG (Retrieval-Augmented Generation)**: Grounds AI responses in real data
        - **GraphRAG**: Knowledge graph queries for relationship insights
        - **RL Trading Agent**: Deep Q-Network for trading signals
        - **Sentiment Analysis**: Real-time news and social media sentiment
        - **Behavioral Analytics**: Trader psychology monitoring

        ### 📊 Features

        - Real-time market data streaming
        - AI-powered conversational analytics
        - ML-based trading recommendations
        - Risk metrics and portfolio analytics
        - Market anomaly detection
        - Multi-modal data fusion (prices, news, social)

        ### 🔐 Security & Compliance

        - Read-only brokerage integration
        - Audit logs for all AI decisions
        - RBAC for user access
        - Rate limiting and monitoring

        ---

        **Version**: 1.0.0 | **Built with**: Python, Apache Stack, LangChain, Streamlit
        """)


if __name__ == "__main__":
    main()
