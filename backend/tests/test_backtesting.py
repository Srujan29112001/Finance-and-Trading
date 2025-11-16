"""
Backtesting Framework Tests

Tests for the backtesting engine and related functionality.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.services.backtesting import BacktestEngine, Action, Trade, Position


class TestBacktestEngine:
    """Test the backtesting engine"""

    @pytest.fixture
    def engine(self):
        """Create a backtest engine instance"""
        return BacktestEngine(
            initial_capital=100000.0,
            commission_pct=0.001,
            slippage_pct=0.0005
        )

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        return pd.DataFrame({
            'timestamp': dates,
            'symbol': ['AAPL'] * 30,
            'price': [150.0 + i for i in range(30)]
        })

    @pytest.fixture
    def sample_signals(self):
        """Create sample trading signals"""
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        actions = ['BUY', 'HOLD'] * 14 + ['SELL', 'HOLD']

        return pd.DataFrame({
            'timestamp': dates,
            'symbol': ['AAPL'] * 30,
            'action': actions,
            'quantity': [100] * 30
        })

    def test_initial_state(self, engine):
        """Test initial engine state"""
        assert engine.cash == 100000.0
        assert engine.get_portfolio_value() == 100000.0
        assert len(engine.positions) == 0
        assert len(engine.trades) == 0

    def test_execute_buy_trade(self, engine):
        """Test executing a buy trade"""
        timestamp = datetime.now()
        success = engine.execute_trade(timestamp, "AAPL", Action.BUY, 100, 150.0)

        assert success
        assert "AAPL" in engine.positions
        assert engine.positions["AAPL"].quantity == 100
        assert engine.cash < 100000.0  # Cash should decrease

    def test_execute_sell_trade(self, engine):
        """Test executing a sell trade"""
        timestamp = datetime.now()

        # First buy
        engine.execute_trade(timestamp, "AAPL", Action.BUY, 100, 150.0)

        # Then sell
        success = engine.execute_trade(timestamp, "AAPL", Action.SELL, 100, 155.0)

        assert success
        assert "AAPL" not in engine.positions  # Position should be closed
        assert engine.cash > 100000.0  # Should have profit

    def test_insufficient_funds(self, engine):
        """Test that trade fails with insufficient funds"""
        timestamp = datetime.now()

        # Try to buy more than we can afford
        success = engine.execute_trade(timestamp, "AAPL", Action.BUY, 100000, 150.0)

        assert not success
        assert len(engine.positions) == 0

    def test_sell_without_position(self, engine):
        """Test that selling without position fails"""
        timestamp = datetime.now()

        success = engine.execute_trade(timestamp, "AAPL", Action.SELL, 100, 150.0)

        assert not success

    def test_position_tracking(self, engine):
        """Test position tracking and average cost"""
        timestamp = datetime.now()

        # Buy 100 shares at $150
        engine.execute_trade(timestamp, "AAPL", Action.BUY, 100, 150.0)

        # Buy 100 more at $160
        engine.execute_trade(timestamp, "AAPL", Action.BUY, 100, 160.0)

        position = engine.positions["AAPL"]
        assert position.quantity == 200
        # Average cost should be around 155 (accounting for slippage/commission)
        assert 154 < position.avg_cost < 156

    def test_portfolio_value_calculation(self, engine):
        """Test portfolio value calculation"""
        timestamp = datetime.now()

        # Buy shares
        engine.execute_trade(timestamp, "AAPL", Action.BUY, 100, 150.0)

        # Update price
        engine.positions["AAPL"].current_price = 160.0

        portfolio_value = engine.get_portfolio_value()

        # Portfolio = cash + (100 shares * $160)
        assert portfolio_value > 100000.0

    def test_run_backtest(self, engine, sample_price_data, sample_signals):
        """Test running a complete backtest"""
        result = engine.run_backtest(
            signals=sample_signals,
            price_data=sample_price_data,
            strategy_name="Test Strategy"
        )

        assert result.strategy_name == "Test Strategy"
        assert result.initial_capital == 100000.0
        assert result.total_trades >= 0
        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'max_drawdown_pct')
        assert len(result.equity_curve) > 0


class TestPosition:
    """Test Position class"""

    def test_position_creation(self):
        """Test creating a position"""
        pos = Position(symbol="AAPL", quantity=100, avg_cost=150.0, current_price=155.0)

        assert pos.symbol == "AAPL"
        assert pos.quantity == 100
        assert pos.avg_cost == 150.0
        assert pos.current_price == 155.0

    def test_position_market_value(self):
        """Test market value calculation"""
        pos = Position(symbol="AAPL", quantity=100, avg_cost=150.0, current_price=155.0)

        assert pos.market_value == 15500.0

    def test_position_unrealized_pnl(self):
        """Test unrealized P/L calculation"""
        pos = Position(symbol="AAPL", quantity=100, avg_cost=150.0, current_price=155.0)

        assert pos.unrealized_pnl == 500.0
        assert pos.unrealized_pnl_pct == pytest.approx(3.333, rel=0.01)


class TestTrade:
    """Test Trade class"""

    def test_trade_creation(self):
        """Test creating a trade record"""
        trade = Trade(
            timestamp=datetime.now(),
            symbol="AAPL",
            action=Action.BUY,
            quantity=100,
            price=150.0,
            commission=15.0
        )

        assert trade.symbol == "AAPL"
        assert trade.action == Action.BUY
        assert trade.quantity == 100
        assert trade.price == 150.0
        assert trade.commission == 15.0
