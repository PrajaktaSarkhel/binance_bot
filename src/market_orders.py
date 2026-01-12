#!/usr/bin/env python3
"""
Market Orders Module
Executes immediate market orders at current market price
"""

import sys
import argparse
from typing import Dict, Optional
from binance.exceptions import BinanceAPIException
from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class MarketOrderExecutor:
    """Handles market order execution on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize market order executor
        
        Args:
            dry_run: If True, simulate order without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
    
    def place_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """
        Place a market order
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            quantity: Order quantity
            
        Returns:
            Order response dict or None if failed
        """
        try:
            # Validate order parameters
            valid, msg, params = OrderValidator.validate_market_order(
                symbol, side, quantity
            )
            
            if not valid:
                log_error(f"Validation failed: {msg}")
                return None
            
            symbol = params['symbol']
            side = params['side']
            quantity = params['quantity']
            
            # Get current price for reference
            current_price = OrderValidator.get_current_price(symbol)
            estimated_value = quantity * current_price
            
            # Display order summary
            print("\n" + "="*60)
            print("MARKET ORDER SUMMARY")
            print("="*60)
            print(f"Symbol:           {symbol}")
            print(f"Side:             {side}")
            print(f"Quantity:         {quantity}")
            print(f"Current Price:    ${current_price:,.2f}")
            print(f"Estimated Value:  ${estimated_value:,.2f} USDT")
            print(f"Mode:             {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
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
                    'type': 'MARKET',
                    'origQty': str(quantity),
                    'status': 'FILLED',
                    'avgPrice': str(current_price)
                }
                return simulated_order
            
            # Place actual order
            log_info(f"Placing market order: {side} {quantity} {symbol}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            # Log order placement
            BotLogger.log_order(
                order_type='MARKET',
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_id=order['orderId'],
                client_order_id=order.get('clientOrderId')
            )
            
            # Check order status
            order_status = self.check_order_status(symbol, order['orderId'])
            
            if order_status:
                executed_qty = float(order_status.get('executedQty', 0))
                avg_price = float(order_status.get('avgPrice', 0))
                
                # Log execution
                BotLogger.log_execution(
                    order_id=order['orderId'],
                    symbol=symbol,
                    side=side,
                    executed_qty=executed_qty,
                    avg_price=avg_price,
                    status=order_status['status']
                )
                
                # Display execution results
                print("\n" + "="*60)
                print("ORDER EXECUTED SUCCESSFULLY")
                print("="*60)
                print(f"Order ID:         {order['orderId']}")
                print(f"Status:           {order_status['status']}")
                print(f"Executed Qty:     {executed_qty}")
                print(f"Average Price:    ${avg_price:,.2f}")
                print(f"Total Value:      ${executed_qty * avg_price:,.2f} USDT")
                print("="*60)
            
            return order
            
        except BinanceAPIException as e:
            error_msg = f"Binance API Error: {e.message} (Code: {e.code})"
            log_error(error_msg, e)
            BotLogger.log_error('API Error', error_msg, e, 
                              symbol=symbol, side=side, quantity=quantity)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_error(error_msg, e)
            BotLogger.log_error('Execution Error', error_msg, e,
                              symbol=symbol, side=side, quantity=quantity)
            return None
    
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
    
    def get_recent_trades(self, symbol: str, limit: int = 5) -> list:
        """
        Get recent trades for the account
        
        Args:
            symbol: Trading pair
            limit: Number of trades to retrieve
            
        Returns:
            List of recent trades
        """
        try:
            trades = self.client.futures_account_trades(
                symbol=symbol,
                limit=limit
            )
            return trades
        except Exception as e:
            log_error(f"Failed to get recent trades: {str(e)}", e)
            return []


def main():
    """Main entry point for market order CLI"""
    parser = argparse.ArgumentParser(
        description='Execute market orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Buy 0.01 BTC at market price
  python market_orders.py BTCUSDT BUY 0.01
  
  # Sell 0.1 ETH at market price
  python market_orders.py ETHUSDT SELL 0.1
  
  # Simulate order without executing
  python market_orders.py BTCUSDT BUY 0.01 --dry-run
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('side', type=str, choices=['BUY', 'SELL', 'buy', 'sell'],
                       help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate order without executing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Create executor
    executor = MarketOrderExecutor(dry_run=args.dry_run)
    
    # Execute order
    order = executor.place_order(
        symbol=args.symbol.upper(),
        side=args.side.upper(),
        quantity=args.quantity
    )
    
    if order:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()