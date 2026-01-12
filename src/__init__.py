"""
Binance Futures Trading Bot
A comprehensive CLI-based trading bot for Binance USDT-M Futures

Modules:
- config: API configuration and client management
- logger: Structured logging system
- validator: Input validation and exchange rules
- market_orders: Market order execution
- limit_orders: Limit order execution
- advanced: Advanced order types and strategies
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "Educational Use Only"

from .config import Config, BinanceClientManager
from .logger import BotLogger
from .validator import OrderValidator

__all__ = [
    'Config',
    'BinanceClientManager',
    'BotLogger',
    'OrderValidator',
]