"""
Logging module for Binance Futures Trading Bot
Provides structured logging with timestamps and error tracking
"""

import logging
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from config import Config


class BotLogger:
    """Custom logger for trading bot operations"""
    
    _logger: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = 'BinanceBot') -> logging.Logger:
        """
        Get or create logger instance
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        if cls._logger is None:
            cls._logger = logging.getLogger(name)
            cls._logger.setLevel(getattr(logging, Config.LOG_LEVEL))
            
            # File handler
            file_handler = logging.FileHandler(Config.LOG_FILE)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(Config.LOG_FORMAT)
            file_handler.setFormatter(file_formatter)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            
            # Add handlers
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(console_handler)
        
        return cls._logger
    
    @classmethod
    def log_order(cls, order_type: str, symbol: str, side: str, 
                  quantity: float, price: Optional[float] = None, 
                  order_id: Optional[int] = None, **kwargs) -> None:
        """
        Log order placement
        
        Args:
            order_type: Type of order (MARKET, LIMIT, etc.)
            symbol: Trading pair
            side: BUY or SELL
            quantity: Order quantity
            price: Order price (if applicable)
            order_id: Exchange order ID
            **kwargs: Additional order parameters
        """
        logger = cls.get_logger()
        
        order_data = {
            'timestamp': datetime.now().isoformat(),
            'order_type': order_type,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'order_id': order_id,
            **kwargs
        }
        
        msg = f"Order placed: {order_type} {symbol} {side} {quantity}"
        if price:
            msg += f" @ {price}"
        if order_id:
            msg += f" - OrderID: {order_id}"
        
        logger.info(msg)
        logger.debug(f"Order details: {json.dumps(order_data, indent=2)}")
    
    @classmethod
    def log_execution(cls, order_id: int, symbol: str, side: str,
                     executed_qty: float, avg_price: float, 
                     status: str, **kwargs) -> None:
        """
        Log order execution
        
        Args:
            order_id: Exchange order ID
            symbol: Trading pair
            side: BUY or SELL
            executed_qty: Executed quantity
            avg_price: Average execution price
            status: Order status
            **kwargs: Additional execution data
        """
        logger = cls.get_logger()
        
        exec_data = {
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id,
            'symbol': symbol,
            'side': side,
            'executed_qty': executed_qty,
            'avg_price': avg_price,
            'status': status,
            **kwargs
        }
        
        msg = f"Order executed: {symbol} {side} {executed_qty} @ {avg_price} - Status: {status}"
        logger.info(msg)
        logger.debug(f"Execution details: {json.dumps(exec_data, indent=2)}")
    
    @classmethod
    def log_error(cls, error_type: str, message: str, 
                  exception: Optional[Exception] = None, **kwargs) -> None:
        """
        Log error with traceback
        
        Args:
            error_type: Type of error
            message: Error message
            exception: Exception object (if available)
            **kwargs: Additional error context
        """
        logger = cls.get_logger()
        
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            **kwargs
        }
        
        if exception:
            error_data['exception'] = str(exception)
            error_data['traceback'] = traceback.format_exc()
        
        logger.error(f"{error_type}: {message}")
        logger.debug(f"Error details: {json.dumps(error_data, indent=2)}")
        
        if exception:
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
    
    @classmethod
    def log_validation(cls, validation_type: str, passed: bool,
                       details: Dict[str, Any]) -> None:
        """
        Log validation results
        
        Args:
            validation_type: Type of validation
            passed: Whether validation passed
            details: Validation details
        """
        logger = cls.get_logger()
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        msg = f"Validation {status}: {validation_type}"
        
        if passed:
            logger.info(msg)
        else:
            logger.warning(msg)
        
        logger.debug(f"Validation details: {json.dumps(details, indent=2)}")
    
    @classmethod
    def log_strategy(cls, strategy_name: str, action: str, **kwargs) -> None:
        """
        Log strategy actions
        
        Args:
            strategy_name: Name of the strategy
            action: Strategy action taken
            **kwargs: Additional strategy data
        """
        logger = cls.get_logger()
        
        strategy_data = {
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'action': action,
            **kwargs
        }
        
        logger.info(f"Strategy [{strategy_name}]: {action}")
        logger.debug(f"Strategy details: {json.dumps(strategy_data, indent=2)}")
    
    @classmethod
    def log_balance(cls, asset: str, balance: float, 
                   locked: Optional[float] = None) -> None:
        """
        Log balance information
        
        Args:
            asset: Asset symbol
            balance: Available balance
            locked: Locked balance (if applicable)
        """
        logger = cls.get_logger()
        
        msg = f"Balance [{asset}]: Available={balance}"
        if locked is not None:
            msg += f", Locked={locked}"
        
        logger.info(msg)
    
    @classmethod
    def log_position(cls, symbol: str, side: str, size: float,
                    entry_price: float, unrealized_pnl: float) -> None:
        """
        Log position information
        
        Args:
            symbol: Trading pair
            side: LONG or SHORT
            size: Position size
            entry_price: Entry price
            unrealized_pnl: Unrealized PnL
        """
        logger = cls.get_logger()
        
        pnl_indicator = "📈" if unrealized_pnl >= 0 else "📉"
        msg = f"Position {pnl_indicator} [{symbol}]: {side} {size} @ {entry_price} | PnL: {unrealized_pnl}"
        
        logger.info(msg)


# Convenience functions
def log_info(message: str) -> None:
    """Log info message"""
    BotLogger.get_logger().info(message)


def log_warning(message: str) -> None:
    """Log warning message"""
    BotLogger.get_logger().warning(message)


def log_error(message: str, exception: Optional[Exception] = None) -> None:
    """Log error message"""
    if exception:
        BotLogger.log_error('General Error', message, exception)
    else:
        BotLogger.get_logger().error(message)


def log_debug(message: str) -> None:
    """Log debug message"""
    BotLogger.get_logger().debug(message)


if __name__ == "__main__":
    # Test logging
    print("Testing logger...\n")
    
    logger = BotLogger.get_logger()
    
    # Test different log types
    BotLogger.log_order('MARKET', 'BTCUSDT', 'BUY', 0.01, order_id=12345)
    BotLogger.log_execution(12345, 'BTCUSDT', 'BUY', 0.01, 50000.0, 'FILLED')
    BotLogger.log_validation('Symbol Check', True, {'symbol': 'BTCUSDT', 'valid': True})
    BotLogger.log_strategy('TWAP', 'Executing slice 1/10', quantity=0.1)
    BotLogger.log_balance('USDT', 1000.50, 250.00)
    BotLogger.log_position('BTCUSDT', 'LONG', 0.5, 48000.0, 1250.50)
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        BotLogger.log_error('Test Error', 'This is a test error', e)
    
    print("\n✅ Log entries written to bot.log")