"""
Enhanced Logging System for Binance Futures Bot
Provides structured logging with multiple levels and formatters
Windows-compatible (no emoji encoding issues)

Author: Prajakta Sarkhel
Date: 2025
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class BotLogger:
    """Centralized logging system for the trading bot"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_file: str = 'bot.log', level: int = logging.DEBUG):
        """Initialize logger with file and console handlers"""
        if BotLogger._logger is not None:
            return
        
        # Create logger
        self.logger = logging.getLogger('BinanceBot')
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # File handler (UTF-8 encoding for emojis)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Console handler (ASCII-safe, no emojis)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # File formatter (with emojis for file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console formatter (ASCII-safe, no emojis)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        fh.setFormatter(file_formatter)
        ch.setFormatter(console_formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        BotLogger._logger = self.logger
    
    @classmethod
    def get_logger(cls):
        """Get logger instance"""
        if cls._logger is None:
            cls()
        return cls._logger
    
    @staticmethod
    def info(message: str):
        """Log info message"""
        logger = BotLogger.get_logger()
        logger.info(message)
    
    @staticmethod
    def success(message: str):
        """Log success message (ASCII-safe)"""
        logger = BotLogger.get_logger()
        logger.info(f"SUCCESS - {message}")
    
    @staticmethod
    def error(message: str):
        """Log error message"""
        logger = BotLogger.get_logger()
        logger.error(message)
    
    @staticmethod
    def warning(message: str):
        """Log warning message"""
        logger = BotLogger.get_logger()
        logger.warning(message)
    
    @staticmethod
    def debug(message: str):
        """Log debug message"""
        logger = BotLogger.get_logger()
        logger.debug(message)
    
    @staticmethod
    def critical(message: str):
        """Log critical message"""
        logger = BotLogger.get_logger()
        logger.critical(message)
    
    @staticmethod
    def log_order(order_type: str, symbol: str, side: str, quantity: float, 
                  price: Optional[float] = None, order_id: Optional[int] = None):
        """Log order placement (ASCII-safe)"""
        logger = BotLogger.get_logger()
        
        price_str = f" @ {price}" if price else ""
        order_id_str = f" (Order ID: {order_id})" if order_id else ""
        
        message = f"Order Placed: {order_type} {symbol} {side} {quantity}{price_str}{order_id_str}"
        logger.info(message)
    
    @staticmethod
    def log_validation(context: str, success: bool, details: dict = None):
        """Log validation results (ASCII-safe)"""
        logger = BotLogger.get_logger()
        
        status = "PASSED" if success else "FAILED"
        message = f"Validation {status}: {context}"
        
        if success:
            logger.info(message)
        else:
            logger.warning(message)
            if details:
                for key, value in details.items():
                    logger.error(f"{key}: {value}")
    
    @staticmethod
    def log_api_call(endpoint: str, method: str = "POST", status: str = "SUCCESS"):
        """Log API calls"""
        logger = BotLogger.get_logger()
        message = f"API Call: {method} {endpoint} - {status}"
        logger.info(message)
    
    @staticmethod
    def log_error_with_trace(error: Exception, context: str = ""):
        """Log error with traceback"""
        logger = BotLogger.get_logger()
        
        if context:
            logger.error(f"Error in {context}: {str(error)}")
        else:
            logger.error(f"Error: {str(error)}")
        
        # Log traceback
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
    
    @staticmethod
    def separator(char: str = "=", length: int = 70):
        """Log separator line"""
        logger = BotLogger.get_logger()
        logger.info(char * length)
    
    @staticmethod
    def header(title: str):
        """Log section header (ASCII-safe)"""
        logger = BotLogger.get_logger()
        BotLogger.separator()
        logger.info(f"  {title}")
        BotLogger.separator()


# Global logger instance
_global_logger = None

def get_logger(log_file: str = 'bot.log') -> logging.Logger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        bot_logger = BotLogger(log_file=log_file)
        _global_logger = bot_logger.logger
    return _global_logger


def init_logging(log_file: str = 'bot.log', level: int = logging.DEBUG):
    """Initialize logging system"""
    global _global_logger
    bot_logger = BotLogger(log_file=log_file, level=level)
    _global_logger = bot_logger.logger
    return _global_logger


# Convenience functions (ASCII-safe)
def log_info(message: str):
    """Log info message"""
    BotLogger.info(message)

def log_success(message: str):
    """Log success message (ASCII-safe)"""
    BotLogger.success(message)

def log_error(message: str):
    """Log error message"""
    BotLogger.error(message)

def log_warning(message: str):
    """Log warning message"""
    BotLogger.warning(message)

def log_debug(message: str):
    """Log debug message"""
    BotLogger.debug(message)


# ASCII-safe symbols for console output
class Symbols:
    """ASCII-safe symbols for Windows console"""
    CHECK = "[OK]"
    CROSS = "[X]"
    ARROW_RIGHT = "->"
    ARROW_UP = "^"
    ARROW_DOWN = "v"
    INFO = "[i]"
    WARNING = "[!]"
    ERROR = "[ERR]"
    SUCCESS = "[SUCCESS]"
    
    @staticmethod
    def format_status(success: bool) -> str:
        """Format status symbol"""
        return Symbols.CHECK if success else Symbols.CROSS


# Example usage and testing
if __name__ == "__main__":
    # Initialize logger
    logger = BotLogger()
    
    # Test different log levels
    BotLogger.header("TESTING LOGGER")
    
    BotLogger.info("This is an info message")
    BotLogger.success("Order executed successfully")
    BotLogger.warning("Low balance detected")
    BotLogger.error("API rate limit exceeded")
    BotLogger.debug("Debug information")
    
    # Test order logging
    BotLogger.log_order(
        order_type="MARKET",
        symbol="BTCUSDT",
        side="BUY",
        quantity=0.001,
        order_id=123456789
    )
    
    # Test validation logging
    BotLogger.log_validation(
        context="Market Order",
        success=True,
        details={"symbol": "BTCUSDT", "quantity": 0.001}
    )
    
    BotLogger.log_validation(
        context="Limit Order",
        success=False,
        details={"error": "Invalid price"}
    )
    
    # Test API call logging
    BotLogger.log_api_call(
        endpoint="/fapi/v1/order",
        method="POST",
        status="SUCCESS"
    )
    
    # Test error with trace
    try:
        raise ValueError("Test error")
    except Exception as e:
        BotLogger.log_error_with_trace(e, context="Test Function")
    
    BotLogger.separator()
    print("\nLogger test completed. Check bot.log for full output.")
    print(f"Symbols test: {Symbols.CHECK} {Symbols.CROSS} {Symbols.ARROW_RIGHT}")