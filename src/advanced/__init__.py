"""
Advanced Trading Strategies Module

This module contains implementations of advanced order types and trading strategies:
- stop_limit: Stop-limit orders for stop-loss and breakout entries
- oco: One-Cancels-the-Other orders for simultaneous TP/SL
- twap: Time-Weighted Average Price execution strategy
- grid_strategy: Automated grid trading for ranging markets
"""

__version__ = "1.0.0"

from .stop_limit import StopLimitOrderExecutor
from .oco import OCOOrderExecutor
from .twap import TWAPExecutor
from .grid_strategy import GridTradingStrategy

__all__ = [
    'StopLimitOrderExecutor',
    'OCOOrderExecutor',
    'TWAPExecutor',
    'GridTradingStrategy',
]