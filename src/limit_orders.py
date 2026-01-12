#!/usr/bin/env python3
"""
Limit Orders Module
Executes limit orders at specified price levels
"""

import sys
import argparse
from typing import Dict, Optional
from binance.exceptions import BinanceAPIException
from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class LimitOrderExecutor:
    """Handles limit order execution on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize limit order executor
        
        Args:
            dry_run: If True, simulate order without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                   price: float, time_in_force: str = 'GTC') -> Optional[Dict]:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Limit price
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Order response dict or None if failed
        """
        try:
            # Validate order parameters
            valid, msg, params = OrderValidator.validate_limit_order(
                symbol, side, quantity, price
            )
            
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            symbol = params['symbol']
            side = params['side']
            quantity = params['quantity']
            price = params['price']
            
            # Get current price for comparison
            current_price = OrderValidator.get_current_price(symbol)
            price_diff = ((price - current_price) / current_price) * 100
            order_value = quantity * price
            
            # Display order summary
            print("\n" + "="*60)
            print("LIMIT ORDER SUMMARY")
            print("="*60)
            print(f"Symbol:           {symbol}")
            print(f"Side:             {side}")
            print(f"Quantity:         {quantity}")
            print(f"Limit Price:      ${price:,.2f}")
            print(f"Current Price:    ${current_price:,.2f}")
            print(f"Price Difference: {price_diff:+.2f}%")
            print(f"Order Value:      ${order_value:,.2f} USDT")
            print(f"Time in Force:    {time_in_force}")
            print(f"Mode:             {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
            # Warning for potentially unfavorable prices
            if side == 'BUY' and price > current_price * 1.05:
                print("\n⚠️  WARNING: Limit price is 5%+ above current market price")
            elif side == 'SELL' and price < current_price * 0.95:
                print("\n⚠️  WARNING: Limit price is 5%+ below current market price")
            
            # Confirmation for live orders
            if not self.dry_run:
                confirm = input("\nConfirm order placement? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    log_info("Order cancelled by user")
                    return None
            
            if self.dry_run:
                # Simulate order
                log_info("DRY RUN: Order simulated successfully")
                simulated_order = {
                    'orderId': 9999999,
                    'symbol': symbol,
                    'side': side,
                    'type': 'LIMIT',
                    'origQty': str(quantity),
                    'price': str(price),
                    'status': 'NEW',
                    'timeInForce': time_in_force
                }
                return simulated_order
            
            # Place actual order
            log_info(f"Placing limit order: {side} {quantity} {symbol} @ ${price}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force
            )
            
            # Log order placement
            BotLogger.log_order(
                order_type='LIMIT',
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_id=order['orderId'],
                client_order_id=order.get('clientOrderId'),
                time_in_force=time_in_force
            )
            
            # Display order details
            print("\n" + "="*60)
            print("ORDER PLACED SUCCESSFULLY")
            print("="*60)
            print(f"Order ID:         {order['orderId']}")
            print(f"Status:           {order['status']}")
            print(f"Client Order ID:  {order.get('clientOrderId', 'N/A')}")
            print("="*60)
            print("\n💡 Tip: Use check_order.py to monitor order status")
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.message} (Code: {e.code})"
            log_error(error_msg, e)
            BotLogger.log_error('API Error', error_msg, e, 
                              symbol=symbol, side=side, 
                              quantity=quantity, price=price)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_error(error_msg, e)
            BotLogger.log_error('Execution Error', error_msg, e,
                              symbol=symbol, side=side, 
                              quantity=quantity, price=price)
            return None
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancel an existing limit order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            log_info(f"Cancelling order {order_id} for {symbol}")
            
            result = self.client.futures_cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            
            log_info(f"Order {order_id} cancelled successfully")
            BotLogger.log_order(
                order_type='CANCEL',
                symbol=symbol,
                side='N/A',
                quantity=0,
                order_id=order_id,
                status=result['status']
            )
            
            return True
            
        except Exception as e:
            log_error(f"Failed to cancel order: {str(e)}", e)
            return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open orders
        
        Args:
            symbol: Trading pair (None for all pairs)
            
        Returns:
            List of open orders
        """
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
            else:
                orders = self.client.futures_get_open_orders()
            
            return orders
            
        except Exception as e:
            log_error(f"Failed to get open orders: {str(e)}", e)
            return []
    
    def check_order_status(self, symbol: str, order_id: int) -> Optional[Dict]:
        """
        Check status of an order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to check
            
        Returns:
            Order status dict or None
        """
        try:
            order = self.client.futures_get_order(
                symbol=symbol,
                orderId=order_id
            )
            return order
        except Exception as e:
            log_error(f"Failed to check order status: {str(e)}", e)
            return None
    
    def modify_order(self, symbol: str, order_id: int, 
                    new_quantity: Optional[float] = None,
                    new_price: Optional[float] = None) -> Optional[Dict]:
        """
        Modify an existing order by cancelling and replacing
        
        Args:
            symbol: Trading pair
            order_id: Order ID to modify
            new_quantity: New quantity (None to keep unchanged)
            new_price: New price (None to keep unchanged)
            
        Returns:
            New order dict or None if failed
        """
        try:
            # Get existing order
            existing_order = self.check_order_status(symbol, order_id)
            if not existing_order:
                log_error("Cannot modify: order not found")
                return None
            
            # Cancel existing order
            if not self.cancel_order(symbol, order_id):
                log_error("Failed to cancel existing order")
                return None
            
            # Place new order with updated parameters
            quantity = new_quantity if new_quantity else float(existing_order['origQty'])
            price = new_price if new_price else float(existing_order['price'])
            
            return self.place_order(
                symbol=symbol,
                side=existing_order['side'],
                quantity=quantity,
                price=price,
                time_in_force=existing_order.get('timeInForce', 'GTC')
            )
            
        except Exception as e:
            log_error(f"Failed to modify order: {str(e)}", e)
            return None


def main():
    """Main entry point for limit order CLI"""
    parser = argparse.ArgumentParser(
        description='Execute limit orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Buy 0.01 BTC at $50,000
  python limit_orders.py BTCUSDT BUY 0.01 50000
  
  # Sell 0.1 ETH at $3,500
  python limit_orders.py ETHUSDT SELL 0.1 3500
  
  # Place order with IOC time in force
  python limit_orders.py BTCUSDT BUY 0.01 50000 --tif IOC
  
  # Simulate order without executing
  python limit_orders.py BTCUSDT BUY 0.01 50000 --dry-run
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('side', type=str, choices=['BUY', 'SELL', 'buy', 'sell'],
                       help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('price', type=float, help='Limit price')
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
    
    # Create executor
    executor = LimitOrderExecutor(dry_run=args.dry_run)
    
    # Execute order
    order = executor.place_order(
        symbol=args.symbol.upper(),
        side=args.side.upper(),
        quantity=args.quantity,
        price=args.price,
        time_in_force=args.tif
    )
    
    if order:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()