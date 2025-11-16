"""
Comprehensive Backtesting Framework

Provides functionality to backtest trading strategies using historical data.
Supports various metrics, portfolio analysis, and risk calculations.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from loguru import logger


class Action(str, Enum):
    """Trading actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Trade:
    """Individual trade record"""
    timestamp: datetime
    symbol: str
    action: Action
    quantity: int
    price: float
    commission: float = 0.0
    notes: str = ""


@dataclass
class Position:
    """Current position in a symbol"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost basis"""
        return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss"""
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized P/L percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float

    # Performance metrics
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Risk metrics
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk (95%)
    cvar_95: float = 0.0  # Conditional VaR (95%)

    # Time series data
    equity_curve: List[float] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    drawdown_series: List[float] = field(default_factory=list)

    # Trade history
    trades: List[Trade] = field(default_factory=list)


class BacktestEngine:
    """
    Backtesting engine for trading strategies

    Features:
    - Support for multiple symbols
    - Realistic commission/slippage simulation
    - Portfolio-level statistics
    - Risk-adjusted metrics
    - Transaction cost modeling
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_pct: float = 0.001,  # 0.1% commission
        slippage_pct: float = 0.0005,  # 0.05% slippage
        risk_free_rate: float = 0.02  # 2% annual risk-free rate
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.risk_free_rate = risk_free_rate

        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_history: List[Tuple[datetime, float]] = []

    def reset(self):
        """Reset backtest state"""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_history = []

    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value

    def execute_trade(
        self,
        timestamp: datetime,
        symbol: str,
        action: Action,
        quantity: int,
        price: float
    ) -> bool:
        """
        Execute a trade

        Returns:
            bool: True if trade was executed successfully
        """
        if action == Action.HOLD:
            return True

        # Apply slippage
        if action == Action.BUY:
            execution_price = price * (1 + self.slippage_pct)
        else:
            execution_price = price * (1 - self.slippage_pct)

        # Calculate commission
        trade_value = quantity * execution_price
        commission = trade_value * self.commission_pct

        if action == Action.BUY:
            # Check if we have enough cash
            total_cost = trade_value + commission
            if total_cost > self.cash:
                logger.warning(f"Insufficient funds for BUY: need ${total_cost:.2f}, have ${self.cash:.2f}")
                return False

            # Execute buy
            self.cash -= total_cost

            if symbol in self.positions:
                # Update existing position
                pos = self.positions[symbol]
                total_shares = pos.quantity + quantity
                total_cost_basis = (pos.quantity * pos.avg_cost) + trade_value
                pos.quantity = total_shares
                pos.avg_cost = total_cost_basis / total_shares
            else:
                # Create new position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=execution_price
                )

            # Update current price
            self.positions[symbol].current_price = price

        elif action == Action.SELL:
            # Check if we have the position
            if symbol not in self.positions:
                logger.warning(f"Cannot SELL {symbol}: no position exists")
                return False

            pos = self.positions[symbol]
            if pos.quantity < quantity:
                logger.warning(f"Cannot SELL {quantity} shares of {symbol}: only have {pos.quantity}")
                return False

            # Execute sell
            self.cash += (trade_value - commission)

            # Update or close position
            pos.quantity -= quantity
            if pos.quantity == 0:
                del self.positions[symbol]

        # Record trade
        trade = Trade(
            timestamp=timestamp,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=execution_price,
            commission=commission
        )
        self.trades.append(trade)

        # Record equity
        self.equity_history.append((timestamp, self.get_portfolio_value()))

        return True

    def run_backtest(
        self,
        signals: pd.DataFrame,
        price_data: pd.DataFrame,
        strategy_name: str = "Custom Strategy"
    ) -> BacktestResult:
        """
        Run backtest with given signals and price data

        Args:
            signals: DataFrame with columns [timestamp, symbol, action, quantity]
            price_data: DataFrame with columns [timestamp, symbol, price]
            strategy_name: Name of the strategy being tested

        Returns:
            BacktestResult with all metrics
        """
        self.reset()

        logger.info(f"Starting backtest for '{strategy_name}'...")
        logger.info(f"Initial capital: ${self.initial_capital:,.2f}")

        # Execute trades according to signals
        for _, signal in signals.iterrows():
            timestamp = signal['timestamp']
            symbol = signal['symbol']
            action = Action(signal['action'])
            quantity = signal.get('quantity', 100)  # Default 100 shares

            # Get price at this timestamp
            price_row = price_data[
                (price_data['timestamp'] == timestamp) &
                (price_data['symbol'] == symbol)
            ]

            if price_row.empty:
                logger.warning(f"No price data for {symbol} at {timestamp}")
                continue

            price = price_row.iloc[0]['price']

            # Update all position prices
            for pos_symbol in self.positions:
                pos_price_row = price_data[
                    (price_data['timestamp'] == timestamp) &
                    (price_data['symbol'] == pos_symbol)
                ]
                if not pos_price_row.empty:
                    self.positions[pos_symbol].current_price = pos_price_row.iloc[0]['price']

            # Execute trade
            self.execute_trade(timestamp, symbol, action, quantity, price)

        # Calculate results
        result = self._calculate_results(strategy_name)

        logger.info(f"Backtest complete. Final capital: ${result.final_capital:,.2f}")
        logger.info(f"Total return: {result.total_return_pct:.2f}%")
        logger.info(f"Sharpe ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Max drawdown: {result.max_drawdown_pct:.2f}%")

        return result

    def _calculate_results(self, strategy_name: str) -> BacktestResult:
        """Calculate all backtest metrics"""

        if not self.equity_history:
            logger.warning("No equity history available")
            return BacktestResult(
                strategy_name=strategy_name,
                start_date=datetime.now(),
                end_date=datetime.now(),
                initial_capital=self.initial_capital,
                final_capital=self.initial_capital
            )

        # Extract equity curve
        timestamps = [t for t, _ in self.equity_history]
        equity_curve = [v for _, v in self.equity_history]

        start_date = timestamps[0]
        end_date = timestamps[-1]
        final_capital = equity_curve[-1]

        # Calculate returns
        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Daily returns
        daily_returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            daily_returns.append(ret)

        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        if years > 0:
            annualized_return = ((final_capital / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return = 0.0

        # Drawdown
        drawdown_series = []
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = peak - value
            drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0

            drawdown_series.append(drawdown_pct)

            if drawdown > max_drawdown:
                max_drawdown = drawdown
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct

        # Volatility and Sharpe ratio
        if daily_returns:
            volatility = np.std(daily_returns) * np.sqrt(252)  # Annualized
            avg_daily_return = np.mean(daily_returns)

            if volatility > 0:
                sharpe_ratio = ((avg_daily_return * 252) - self.risk_free_rate) / volatility
            else:
                sharpe_ratio = 0.0

            # Sortino ratio (downside deviation)
            negative_returns = [r for r in daily_returns if r < 0]
            if negative_returns:
                downside_std = np.std(negative_returns) * np.sqrt(252)
                if downside_std > 0:
                    sortino_ratio = ((avg_daily_return * 252) - self.risk_free_rate) / downside_std
                else:
                    sortino_ratio = 0.0
            else:
                sortino_ratio = sharpe_ratio
        else:
            volatility = 0.0
            sharpe_ratio = 0.0
            sortino_ratio = 0.0

        # Trade statistics
        winning_trades = []
        losing_trades = []

        for i in range(len(self.trades) - 1):
            trade = self.trades[i]
            if trade.action == Action.BUY:
                # Find corresponding sell
                for j in range(i + 1, len(self.trades)):
                    next_trade = self.trades[j]
                    if next_trade.symbol == trade.symbol and next_trade.action == Action.SELL:
                        pnl = (next_trade.price - trade.price) * trade.quantity - trade.commission - next_trade.commission
                        if pnl > 0:
                            winning_trades.append(pnl)
                        else:
                            losing_trades.append(pnl)
                        break

        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0

        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Risk metrics
        if daily_returns:
            var_95 = np.percentile(daily_returns, 5)  # 5th percentile
            cvar_95 = np.mean([r for r in daily_returns if r <= var_95])
        else:
            var_95 = 0.0
            cvar_95 = 0.0

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate * 100,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            volatility=volatility * 100,
            var_95=var_95 * 100,
            cvar_95=cvar_95 * 100,
            equity_curve=equity_curve,
            daily_returns=[r * 100 for r in daily_returns],  # Convert to percentage
            drawdown_series=drawdown_series,
            trades=self.trades
        )
