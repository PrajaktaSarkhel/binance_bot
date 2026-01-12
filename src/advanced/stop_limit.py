#!/usr/bin/env python3
"""
Stop-Limit Orders Module
Triggers a limit order when stop price is reached
"""

import sys
import argparse
from typing import Dict, Optional
from binance.exceptions import BinanceAPIException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class StopLimitOrderExecutor:
    """Handles stop-limit order execution on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize stop-limit order executor
        
        Args:
            dry_run: If True, simulate order without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
    
    def place_order(self, symbol: str, side: str, quantity: float,
                   stop_price: float, limit_price: float,
                   time_in_force: str = 'GTC') -> Optional[Dict]:
        """
        Place a stop-limit order
        
        Stop-limit orders are triggered when the market price reaches the stop price,
        then a limit order is placed at the specified limit price.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            stop_price: Price that triggers the limit order
            limit_price: Limit price for the triggered order
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Order response dict or None if failed
        """
        try:
            # Validate basic parameters
            valid, msg = OrderValidator.validate_symbol(symbol)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            valid, msg = OrderValidator.validate_side(side)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            # Validate and round quantity
            valid, msg, quantity = OrderValidator.validate_quantity(symbol, quantity)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            # Validate and round prices
            valid, msg, stop_price = OrderValidator.validate_price(symbol, stop_price)
            if not valid:
                log_error(f"Stop price validation failed: {msg}")
                return None
            
            valid, msg, limit_price = OrderValidator.validate_price(symbol, limit_price)
            if not valid:
                log_error(f"Limit price validation failed: {msg}")
                return None
            
            # Validate notional with limit price
            valid, msg = OrderValidator.validate_notional(symbol, quantity, limit_price)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            # Get current price for reference
            current_price = OrderValidator.get_current_price(symbol)
            order_value = quantity * limit_price
            
            # Validate stop-limit logic
            if side == 'SELL':
                # Stop-loss sell: stop_price should be below current, limit below stop
                if stop_price >= current_price:
                    print(f"\n⚠️  Warning: SELL stop price (${stop_price:,.2f}) is at or above current price (${current_price:,.2f})")
                    print("    This will trigger immediately!")
                if limit_price > stop_price:
                    print(f"\n⚠️  Warning: Limit price (${limit_price:,.2f}) is above stop price (${stop_price:,.2f})")
                    print("    Typical stop-loss has limit price <= stop price")
            else:  # BUY
                # Stop-buy: stop_price should be above current, limit above stop
                if stop_price <= current_price:
                    print(f"\n⚠️  Warning: BUY stop price (${stop_price:,.2f}) is at or below current price (${current_price:,.2f})")
                    print("    This will trigger immediately!")
                if limit_price < stop_price:
                    print(f"\n⚠️  Warning: Limit price (${limit_price:,.2f}) is below stop price (${stop_price:,.2f})")
                    print("    Typical stop-buy has limit price >= stop price")
            
            # Display order summary
            print("\n" + "="*60)
            print("STOP-LIMIT ORDER SUMMARY")
            print("="*60)
            print(f"Symbol:           {symbol}")
            print(f"Side:             {side}")
            print(f"Quantity:         {quantity}")
            print(f"Stop Price:       ${stop_price:,.2f}")
            print(f"Limit Price:      ${limit_price:,.2f}")
            print(f"Current Price:    ${current_price:,.2f}")
            print(f"Order Value:      ${order_value:,.2f} USDT")
            print(f"Time in Force:    {time_in_force}")
            print(f"Mode:             {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
            # Explain the order
            if side == 'SELL':
                print(f"\n📊 When price drops to ${stop_price:,.2f},")
                print(f"   a SELL limit order will be placed at ${limit_price:,.2f}")
            else:
                print(f"\n📊 When price rises to ${stop_price:,.2f},")
                print(f"   a BUY limit order will be placed at ${limit_price:,.2f}")
            
            # Confirmation for live orders
            if not self.dry_run:
                confirm = input("\nConfirm order placement? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    log_info("Order cancelled by user")
                    return None
            
            if self.dry_run:
                # Simulate order
                log_info("DRY RUN: Stop-limit order simulated successfully")
                simulated_order = {
                    'orderId': 9999999,
                    'symbol': symbol,
                    'side': side,
                    'type': 'STOP',
                    'origQty': str(quantity),
                    'stopPrice': str(stop_price),
                    'price': str(limit_price),
                    'status': 'NEW',
                    'timeInForce': time_in_force
                }
                return simulated_order
            
            # Place actual order
            log_info(f"Placing stop-limit order: {side} {quantity} {symbol}")
            log_info(f"Stop: ${stop_price}, Limit: ${limit_price}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                quantity=quantity,
                price=limit_price,
                stopPrice=stop_price,
                timeInForce=time_in_force
            )
            
            # Log order placement
            BotLogger.log_order(
                order_type='STOP_LIMIT',
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price,
                order_id=order['orderId'],
                client_order_id=order.get('clientOrderId'),
                stop_price=stop_price,
                time_in_force=time_in_force
            )
            
            # Display order details
            print("\n" + "="*60)
            print("STOP-LIMIT ORDER PLACED SUCCESSFULLY")
            print("="*60)
            print(f"Order ID:         {order['orderId']}")
            print(f"Status:           {order['status']}")
            print(f"Client Order ID:  {order.get('clientOrderId', 'N/A')}")
            print("="*60)
            print("\n💡 Order will be triggered when market reaches stop price")
            print("💡 Use check_order.py to monitor order status")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.message} (Code: {e.code})"
            log_error(error_msg, e)
            BotLogger.log_error('API Error', error_msg, e, 
                              symbol=symbol, side=side, 
                              quantity=quantity, stop_price=stop_price,
                              limit_price=limit_price)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_error(error_msg, e)
            BotLogger.log_error('Execution Error', error_msg, e,
                              symbol=symbol, side=side, 
                              quantity=quantity, stop_price=stop_price,
                              limit_price=limit_price)
            return None
    
    def place_stop_loss(self, symbol: str, quantity: float,
                       stop_price: float, limit_offset: float = 0.001) -> Optional[Dict]:
        """
        Convenience method to place a stop-loss order
        
        Args:
            symbol: Trading pair
            quantity: Order quantity
            stop_price: Stop loss trigger price
            limit_offset: Offset below stop price for limit (default 0.1%)
            
        Returns:
            Order response dict or None if failed
        """
        limit_price = stop_price * (1 - limit_offset)
        
        print("\n🛡️  Placing STOP-LOSS order")
        
        return self.place_order(
            symbol=symbol,
            side='SELL',
            quantity=quantity,
            stop_price=stop_price,
            limit_price=limit_price
        )
    
    def place_stop_buy(self, symbol: str, quantity: float,
                      stop_price: float, limit_offset: float = 0.001) -> Optional[Dict]:
        """
        Convenience method to place a stop-buy order (breakout entry)
        
        Args:
            symbol: Trading pair
            quantity: Order quantity
            stop_price: Stop buy trigger price
            limit_offset: Offset above stop price for limit (default 0.1%)
            
        Returns:
            Order response dict or None if failed
        """
        limit_price = stop_price * (1 + limit_offset)
        
        print("\n📈 Placing STOP-BUY order (breakout entry)")
        
        return self.place_order(
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            stop_price=stop_price,
            limit_price=limit_price
        )


def main():
    """Main entry point for stop-limit order CLI"""
    parser = argparse.ArgumentParser(
        description='Execute stop-limit orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stop-loss: Sell if price drops to $49,000 (limit at $48,900)
  python stop_limit.py BTCUSDT SELL 0.01 49000 48900
  
  # Stop-buy: Buy if price rises to $51,000 (limit at $51,100)
  python stop_limit.py BTCUSDT BUY 0.01 51000 51100
  
  # Quick stop-loss with auto-calculated limit
  python stop_limit.py BTCUSDT SELL 0.01 49000 --auto-limit
  
  # Simulate order without executing
  python stop_limit.py BTCUSDT SELL 0.01 49000 48900 --dry-run

Use Cases:
  - Stop-loss: Protect profits or limit losses on existing positions
  - Stop-buy: Enter on breakouts above resistance levels
  - Trailing stops: Manually adjust stop price as market moves favorably
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('side', type=str, choices=['BUY', 'SELL', 'buy', 'sell'],
                       help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('stop_price', type=float, help='Stop trigger price')
    parser.add_argument('limit_price', type=float, nargs='?',
                       help='Limit price (optional with --auto-limit)')
    parser.add_argument('--auto-limit', action='store_true',
                       help='Auto-calculate limit price (0.1%% offset from stop)')
    parser.add_argument('--tif', '--time-in-force', type=str,
                       choices=['GTC', 'IOC', 'FOK'], default='GTC',
                       help='Time in force (default: GTC)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate order without executing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Calculate limit price if auto-limit enabled
    if args.auto_limit:
        if args.side.upper() == 'SELL':
            limit_price = args.stop_price * 0.999  # 0.1% below stop
        else:
            limit_price = args.stop_price * 1.001  # 0.1% above stop
        print(f"\n🔧 Auto-calculated limit price: ${limit_price:,.2f}")
    else:
        if args.limit_price is None:
            print("\n❌ Error: limit_price required (or use --auto-limit)")
            sys.exit(1)
        limit_price = args.limit_price
    
    # Create executor
    executor = StopLimitOrderExecutor(dry_run=args.dry_run)
    
    # Execute order
    order = executor.place_order(
        symbol=args.symbol.upper(),
        side=args.side.upper(),
        quantity=args.quantity,
        stop_price=args.stop_price,
        limit_price=limit_price,
        time_in_force=args.tif
    )
    
    if order:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()