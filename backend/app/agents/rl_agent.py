"""
Reinforcement Learning Trading Agent (DQN-based)
"""

import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
import os
import pickle

# RL imports
try:
    import torch
    import torch.nn as nn
    from stable_baselines3 import DQN
    from stable_baselines3.common.vec_env import DummyVecEnv
    HAS_RL = True
except ImportError:
    logger.warning("RL libraries not available. Using mock RL agent.")
    HAS_RL = False

from app.config import settings


class MockRLAgent:
    """Mock RL agent for when dependencies are not available."""

    async def generate_signal(self, symbol: str) -> Dict[str, Any]:
        """Generate a mock trading signal."""
        # Simple heuristic-based signal
        import random

        actions = ["BUY", "HOLD", "SELL"]
        action = random.choice(actions)
        confidence = random.uniform(0.6, 0.9)

        # Mock prices
        price = 100.0 + random.uniform(-10, 10)
        target_price = price * (1.05 if action == "BUY" else 0.95)
        stop_loss = price * (0.97 if action == "BUY" else 1.03)

        return {
            "symbol": symbol.upper(),
            "signal_type": action,
            "confidence": round(confidence, 4),
            "price": round(price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "reasoning": f"Mock signal generated based on heuristics. Confidence: {confidence:.1%}",
            "timestamp": datetime.utcnow()
        }


class TradingEnvironment:
    """
    Simple trading environment for RL agent.
    This is a basic implementation - production would use more sophisticated features.
    """

    def __init__(self, symbol: str, historical_data: np.ndarray):
        self.symbol = symbol
        self.data = historical_data
        self.current_step = 0
        self.max_steps = len(historical_data) - 1
        self.position = 0  # -1: short, 0: neutral, 1: long
        self.cash = 10000.0
        self.shares = 0
        self.initial_cash = 10000.0

    def reset(self):
        """Reset environment to initial state."""
        self.current_step = 0
        self.position = 0
        self.cash = self.initial_cash
        self.shares = 0
        return self._get_observation()

    def _get_observation(self):
        """Get current state observation."""
        # Features: price, volume, position, cash ratio
        if self.current_step >= len(self.data):
            self.current_step = len(self.data) - 1

        price = self.data[self.current_step, 0]
        volume = self.data[self.current_step, 1] if self.data.shape[1] > 1 else 1000

        obs = np.array([
            price,
            volume,
            self.position,
            self.cash / self.initial_cash,
            self.shares
        ])

        return obs

    def step(self, action):
        """
        Execute action and return next state, reward, done.
        Actions: 0=SELL, 1=HOLD, 2=BUY
        """
        price = self.data[self.current_step, 0]

        # Execute action
        reward = 0

        if action == 2 and self.cash >= price:  # BUY
            shares_to_buy = int(self.cash / price)
            self.shares += shares_to_buy
            self.cash -= shares_to_buy * price
            self.position = 1
        elif action == 0 and self.shares > 0:  # SELL
            self.cash += self.shares * price
            self.shares = 0
            self.position = 0

        # Move to next step
        self.current_step += 1

        if self.current_step >= self.max_steps:
            done = True
            # Final reward based on total portfolio value
            final_value = self.cash + (self.shares * price if self.current_step < len(self.data) else 0)
            reward = (final_value - self.initial_cash) / self.initial_cash
        else:
            done = False
            # Reward based on portfolio change
            current_value = self.cash + self.shares * self.data[self.current_step, 0]
            prev_value = self.cash + self.shares * price
            reward = (current_value - prev_value) / prev_value if prev_value > 0 else 0

        obs = self._get_observation()

        return obs, reward, done, {}


class RLTradingAgent:
    """
    Reinforcement Learning agent for generating trading signals.
    Uses DQN (Deep Q-Network) algorithm.
    """

    def __init__(self):
        """Initialize the RL agent."""
        self.model_path = settings.RL_MODEL_PATH
        self.model = None

        if HAS_RL:
            self._load_or_create_model()
        else:
            logger.warning("Using mock RL agent")

        logger.info("RL Trading Agent initialized")

    def _load_or_create_model(self):
        """Load existing model or create a new one."""
        try:
            if os.path.exists(f"{self.model_path}/model.zip"):
                self.model = DQN.load(f"{self.model_path}/model.zip")
                logger.info(f"✓ Loaded RL model from {self.model_path}")
            else:
                logger.info("No existing model found. Model will be trained on first use.")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading RL model: {e}")
            self.model = None

    async def generate_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Generate a trading signal for the given symbol.
        """
        try:
            if not HAS_RL or self.model is None:
                # Use mock agent
                mock_agent = MockRLAgent()
                return await mock_agent.generate_signal(symbol)

            # Get current market state
            state = await self._get_current_state(symbol)

            if state is None:
                return await MockRLAgent().generate_signal(symbol)

            # Get action from model
            action, _states = self.model.predict(state, deterministic=True)

            # Map action to signal
            action_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
            signal_type = action_map[int(action)]

            # Get current price
            from app.database import async_session_maker
            from app.models.market import LatestStockPrice
            from sqlalchemy import select

            async with async_session_maker() as session:
                query = select(LatestStockPrice).where(
                    LatestStockPrice.symbol == symbol.upper()
                )
                result = await session.execute(query)
                price_data = result.scalar_one_or_none()

                if not price_data:
                    return await MockRLAgent().generate_signal(symbol)

                current_price = float(price_data.close)

            # Calculate target and stop loss
            if signal_type == "BUY":
                target_price = current_price * 1.05  # 5% profit target
                stop_loss = current_price * 0.97  # 3% stop loss
                confidence = 0.75
            elif signal_type == "SELL":
                target_price = current_price * 0.95
                stop_loss = current_price * 1.03
                confidence = 0.70
            else:  # HOLD
                target_price = current_price
                stop_loss = current_price
                confidence = 0.65

            return {
                "symbol": symbol.upper(),
                "signal_type": signal_type,
                "confidence": round(confidence, 4),
                "price": round(current_price, 2),
                "target_price": round(target_price, 2),
                "stop_loss": round(stop_loss, 2),
                "reasoning": f"Signal generated by DQN reinforcement learning model based on market state analysis.",
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error generating RL signal: {e}")
            # Fallback to mock
            mock_agent = MockRLAgent()
            return await mock_agent.generate_signal(symbol)

    async def _get_current_state(self, symbol: str) -> Optional[np.ndarray]:
        """Get current market state for the model."""
        try:
            from app.database import async_session_maker
            from app.models.market import StockPrice
            from sqlalchemy import select

            async with async_session_maker() as session:
                # Get recent price history
                query = select(StockPrice).where(
                    StockPrice.symbol == symbol.upper()
                ).order_by(StockPrice.timestamp.desc()).limit(10)

                result = await session.execute(query)
                prices = result.scalars().all()

                if not prices:
                    return None

                # Build state vector
                latest = prices[0]
                state = np.array([
                    float(latest.close),
                    float(latest.volume),
                    0,  # position (unknown in live trading)
                    1.0,  # cash ratio
                    0  # shares
                ])

                return state

        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return None

    async def train(self, symbol: str, episodes: int = 1000):
        """
        Train the RL agent on historical data.
        This would typically be run offline or periodically.
        """
        if not HAS_RL:
            logger.warning("Cannot train: RL libraries not available")
            return

        try:
            logger.info(f"Training RL agent for {symbol}...")

            # Get historical data
            from app.database import async_session_maker
            from app.models.market import StockPrice
            from sqlalchemy import select

            async with async_session_maker() as session:
                query = select(StockPrice).where(
                    StockPrice.symbol == symbol.upper()
                ).order_by(StockPrice.timestamp.asc()).limit(1000)

                result = await session.execute(query)
                prices = result.scalars().all()

                if len(prices) < 100:
                    logger.warning("Not enough data to train")
                    return

                # Prepare data
                data = np.array([[float(p.close), float(p.volume)] for p in prices])

                # Create environment
                env = TradingEnvironment(symbol, data)

                # Create or update model
                if self.model is None:
                    self.model = DQN(
                        "MlpPolicy",
                        env,
                        verbose=1,
                        learning_rate=0.0001,
                        buffer_size=10000,
                        learning_starts=100,
                        batch_size=32,
                        tau=0.005,
                        gamma=0.99,
                        train_freq=4,
                        gradient_steps=1,
                        target_update_interval=100
                    )

                # Train
                self.model.learn(total_timesteps=episodes)

                # Save model
                os.makedirs(self.model_path, exist_ok=True)
                self.model.save(f"{self.model_path}/model.zip")

                logger.info(f"✓ RL agent trained and saved to {self.model_path}")

        except Exception as e:
            logger.error(f"Error training RL agent: {e}")


# Singleton instance
_rl_agent_instance = None


def get_rl_agent() -> RLTradingAgent:
    """Get or create the RL agent singleton."""
    global _rl_agent_instance
    if _rl_agent_instance is None:
        _rl_agent_instance = RLTradingAgent()
    return _rl_agent_instance
