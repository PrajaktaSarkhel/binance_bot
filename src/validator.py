"""
Validation module for Binance Futures Trading Bot
Validates symbols, quantities, prices, and other order parameters
"""

from typing import Dict, Tuple, Optional
from decimal import Decimal, ROUND_DOWN
from binance.exceptions import BinanceAPIException
from config import BinanceClientManager, Config
from logger import BotLogger


class OrderValidator:
    """Validates order parameters against Binance exchange rules"""
    
    # Cache for exchange info
    _exchange_info: Optional[Dict] = None
    _symbol_info_cache: Dict[str, Dict] = {}
    
    @classmethod
    def get_exchange_info(cls) -> Dict:
        """Get and cache exchange information"""
        if cls._exchange_info is None:
            client = BinanceClientManager.get_client()
            cls._exchange_info = client.futures_exchange_info()
        return cls._exchange_info
    
    @classmethod
    def get_symbol_info(cls, symbol: str) -> Optional[Dict]:
        """
        Get symbol information from exchange
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Symbol info dict or None if not found
        """
        if symbol not in cls._symbol_info_cache:
            exchange_info = cls.get_exchange_info()
            
            for sym in exchange_info['symbols']:
                if sym['symbol'] == symbol:
                    cls._symbol_info_cache[symbol] = sym
                    break
        
        return cls._symbol_info_cache.get(symbol)
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> Tuple[bool, str]:
        """
        Validate trading symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        symbol = symbol.upper()
        
        # Check format
        if not symbol.endswith('USDT'):
            return False, "Symbol must be a USDT-M Futures pair (e.g., BTCUSDT)"
        
        # Check if symbol exists
        symbol_info = cls.get_symbol_info(symbol)
        if not symbol_info:
            return False, f"Symbol {symbol} not found on Binance Futures"
        
        # Check if trading is enabled
        if symbol_info['status'] != 'TRADING':
            return False, f"Trading is not enabled for {symbol}"
        
        BotLogger.log_validation('Symbol', True, {
            'symbol': symbol,
            'status': symbol_info['status']
        })
        
        return True, ""
    
    @classmethod
    def validate_side(cls, side: str) -> Tuple[bool, str]:
        """
        Validate order side
        
        Args:
            side: Order side (BUY/SELL)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        side = side.upper()
        
        if side not in ['BUY', 'SELL']:
            return False, "Side must be either 'BUY' or 'SELL'"
        
        return True, ""
    
    @classmethod
    def get_filters(cls, symbol: str) -> Dict[str, Dict]:
        """
        Get all filters for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary of filters by type
        """
        symbol_info = cls.get_symbol_info(symbol)
        if not symbol_info:
            return {}
        
        filters = {}
        for f in symbol_info.get('filters', []):
            filters[f['filterType']] = f
        
        return filters
    
    @classmethod
    def validate_quantity(cls, symbol: str, quantity: float) -> Tuple[bool, str, float]:
        """
        Validate and round quantity according to exchange rules
        
        Args:
            symbol: Trading pair symbol
            quantity: Order quantity
            
        Returns:
            Tuple of (is_valid, error_message, rounded_quantity)
        """
        filters = cls.get_filters(symbol)
        
        # LOT_SIZE filter
        lot_size = filters.get('LOT_SIZE', {})
        min_qty = float(lot_size.get('minQty', 0))
        max_qty = float(lot_size.get('maxQty', float('inf')))
        step_size = float(lot_size.get('stepSize', 0))
        
        if quantity < min_qty:
            return False, f"Quantity {quantity} below minimum {min_qty}", 0
        
        if quantity > max_qty:
            return False, f"Quantity {quantity} exceeds maximum {max_qty}", 0
        
        # Round to step size
        if step_size > 0:
            precision = len(str(step_size).rstrip('0').split('.')[-1])
            quantity = float(Decimal(str(quantity)).quantize(
                Decimal(str(step_size)), 
                rounding=ROUND_DOWN
            ))
        
        BotLogger.log_validation('Quantity', True, {
            'symbol': symbol,
            'quantity': quantity,
            'min_qty': min_qty,
            'max_qty': max_qty,
            'step_size': step_size
        })
        
        return True, "", quantity
    
    @classmethod
    def validate_price(cls, symbol: str, price: float) -> Tuple[bool, str, float]:
        """
        Validate and round price according to exchange rules
        
        Args:
            symbol: Trading pair symbol
            price: Order price
            
        Returns:
            Tuple of (is_valid, error_message, rounded_price)
        """
        filters = cls.get_filters(symbol)
        
        # PRICE_FILTER
        price_filter = filters.get('PRICE_FILTER', {})
        min_price = float(price_filter.get('minPrice', 0))
        max_price = float(price_filter.get('maxPrice', float('inf')))
        tick_size = float(price_filter.get('tickSize', 0))
        
        if price < min_price:
            return False, f"Price {price} below minimum {min_price}", 0
        
        if price > max_price:
            return False, f"Price {price} exceeds maximum {max_price}", 0
        
        # Round to tick size
        if tick_size > 0:
            precision = len(str(tick_size).rstrip('0').split('.')[-1])
            price = float(Decimal(str(price)).quantize(
                Decimal(str(tick_size)), 
                rounding=ROUND_DOWN
            ))
        
        BotLogger.log_validation('Price', True, {
            'symbol': symbol,
            'price': price,
            'min_price': min_price,
            'max_price': max_price,
            'tick_size': tick_size
        })
        
        return True, "", price
    
    @classmethod
    def validate_notional(cls, symbol: str, quantity: float, price: float) -> Tuple[bool, str]:
        """
        Validate order notional value (quantity * price)
        
        Args:
            symbol: Trading pair symbol
            quantity: Order quantity
            price: Order price
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        filters = cls.get_filters(symbol)
        
        # MIN_NOTIONAL filter
        min_notional_filter = filters.get('MIN_NOTIONAL', {})
        min_notional = float(min_notional_filter.get('notional', 0))
        
        notional = quantity * price
        
        if notional < min_notional:
            return False, f"Order value {notional} USDT below minimum {min_notional} USDT"
        
        # Check against safety limits
        if notional > Config.MAX_ORDER_VALUE_USD:
            return False, f"Order value {notional} USDT exceeds safety limit {Config.MAX_ORDER_VALUE_USD} USDT"
        
        if notional < Config.MIN_ORDER_VALUE_USD:
            return False, f"Order value {notional} USDT below minimum {Config.MIN_ORDER_VALUE_USD} USDT"
        
        BotLogger.log_validation('Notional', True, {
            'symbol': symbol,
            'notional_value': notional,
            'min_notional': min_notional
        })
        
        return True, ""
    
    @classmethod
    def validate_market_order(cls, symbol: str, side: str, quantity: float) -> Tuple[bool, str, Dict]:
        """
        Validate market order parameters
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            
        Returns:
            Tuple of (is_valid, error_message, validated_params)
        """
        # Validate symbol
        valid, msg = cls.validate_symbol(symbol)
        if not valid:
            BotLogger.log_validation('Market Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate side
        valid, msg = cls.validate_side(side)
        if not valid:
            BotLogger.log_validation('Market Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate and round quantity
        valid, msg, rounded_qty = cls.validate_quantity(symbol, quantity)
        if not valid:
            BotLogger.log_validation('Market Order', False, {'error': msg})
            return False, msg, {}
        
        validated_params = {
            'symbol': symbol,
            'side': side.upper(),
            'quantity': rounded_qty
        }
        
        BotLogger.log_validation('Market Order', True, validated_params)
        return True, "", validated_params
    
    @classmethod
    def validate_limit_order(cls, symbol: str, side: str, quantity: float, price: float) -> Tuple[bool, str, Dict]:
        """
        Validate limit order parameters
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Order price
            
        Returns:
            Tuple of (is_valid, error_message, validated_params)
        """
        # Validate symbol
        valid, msg = cls.validate_symbol(symbol)
        if not valid:
            BotLogger.log_validation('Limit Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate side
        valid, msg = cls.validate_side(side)
        if not valid:
            BotLogger.log_validation('Limit Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate and round quantity
        valid, msg, rounded_qty = cls.validate_quantity(symbol, quantity)
        if not valid:
            BotLogger.log_validation('Limit Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate and round price
        valid, msg, rounded_price = cls.validate_price(symbol, price)
        if not valid:
            BotLogger.log_validation('Limit Order', False, {'error': msg})
            return False, msg, {}
        
        # Validate notional
        valid, msg = cls.validate_notional(symbol, rounded_qty, rounded_price)
        if not valid:
            BotLogger.log_validation('Limit Order', False, {'error': msg})
            return False, msg, {}
        
        validated_params = {
            'symbol': symbol,
            'side': side.upper(),
            'quantity': rounded_qty,
            'price': rounded_price
        }
        
        BotLogger.log_validation('Limit Order', True, validated_params)
        return True, "", validated_params
    
    @classmethod
    def get_current_price(cls, symbol: str) -> float:
        """
        Get current market price for symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Current price
        """
        client = BinanceClientManager.get_client()
        ticker = client.futures_symbol_ticker(symbol=symbol)
        return float(ticker['price'])


if __name__ == "__main__":
    # Test validator
    print("Testing validator...\n")
    
    # Test symbol validation
    valid, msg = OrderValidator.validate_symbol('BTCUSDT')
    print(f"BTCUSDT validation: {valid} - {msg}")
    
    # Test quantity validation
    valid, msg, qty = OrderValidator.validate_quantity('BTCUSDT', 0.01)
    print(f"Quantity 0.01: {valid} - Rounded: {qty}")
    
    # Test market order validation
    valid, msg, params = OrderValidator.validate_market_order('BTCUSDT', 'BUY', 0.01)
    print(f"Market order validation: {valid}")
    print(f"Validated params: {params}")
    
    # Test limit order validation
    valid, msg, params = OrderValidator.validate_limit_order('BTCUSDT', 'BUY', 0.01, 50000.0)
    print(f"Limit order validation: {valid}")
    print(f"Validated params: {params}")
    
    print("\n✅ Validation tests complete")