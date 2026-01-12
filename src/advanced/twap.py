#!/usr/bin/env python3
"""
TWAP (Time-Weighted Average Price) Strategy Module
Splits large orders into smaller chunks executed over time
"""

import sys
import argparse
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class TWAPExecutor:
    """Executes TWAP strategy on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize TWAP executor
        
        Args:
            dry_run: If True, simulate orders without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
        self.executed_orders = []
    
    def execute_twap(self, symbol: str, side: str, total_quantity: float,
                    duration_minutes: int, num_intervals: int,
                    limit_price: Optional[float] = None) -> List[Dict]:
        """
        Execute TWAP strategy
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            total_quantity: Total quantity to execute
            duration_minutes: Total duration in minutes
            num_intervals: Number of order slices
            limit_price: Optional limit price for orders (None = market orders)
            
        Returns:
            List of executed orders
        """
        try:
            # Validate parameters
            valid, msg = OrderValidator.validate_symbol(symbol)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return []
            
            valid, msg = OrderValidator.validate_side(side)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return []
            
            # Calculate slice size
            slice_quantity = total_quantity / num_intervals
            
            # Validate slice quantity
            valid, msg, slice_quantity = OrderValidator.validate_quantity(symbol, slice_quantity)
            if not valid:
                log_error(f"Slice quantity validation failed: {msg}")
                return []
            
            # Recalculate actual total based on rounded slices
            actual_total = slice_quantity * num_intervals
            
            # Calculate interval duration
            interval_seconds = (duration_minutes * 60) / num_intervals
            
            # Get starting price
            start_price = OrderValidator.get_current_price(symbol)
            estimated_value = actual_total * start_price
            
            # Display TWAP summary
            print("\n" + "="*60)
            print("TWAP STRATEGY SUMMARY")
            print("="*60)
            print(f"Symbol:               {symbol}")
            print(f"Side:                 {side}")
            print(f"Total Quantity:       {actual_total:.8f} (requested: {total_quantity})")
            print(f"Slice Quantity:       {slice_quantity:.8f}")
            print(f"Number of Slices:     {num_intervals}")
            print(f"Total Duration:       {duration_minutes} minutes")
            print(f"Interval:             {interval_seconds:.1f} seconds")
            print(f"Order Type:           {'LIMIT' if limit_price else 'MARKET'}")
            if limit_price:
                print(f"Limit Price:          ${limit_price:,.2f}")
            print(f"Starting Price:       ${start_price:,.2f}")
            print(f"Estimated Value:      ${estimated_value:,.2f} USDT")
            print(f"Mode:                 {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
            # Calculate estimated completion time
            completion_time = datetime.now() + timedelta(minutes=duration_minutes)
            print(f"\n⏰ Estimated completion: {completion_time.strftime('%H:%M:%S')}")
            
            # Confirmation for live orders
            if not self.dry_run:
                confirm = input("\nConfirm TWAP execution? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    log_info("TWAP execution cancelled by user")
                    return []
            
            # Log TWAP start
            BotLogger.log_strategy(
                strategy_name='TWAP',
                action='Starting Execution',
                symbol=symbol,
                side=side,
                total_quantity=actual_total,
                num_intervals=num_intervals,
                duration_minutes=duration_minutes
            )
            
            print("\n" + "="*60)
            print("EXECUTING TWAP STRATEGY")
            print("="*60)
            
            # Execute slices
            for i in range(num_intervals):
                slice_num = i + 1
                
                # Get current price
                current_price = OrderValidator.get_current_price(symbol)
                
                # Display progress
                progress = (slice_num / num_intervals) * 100
                print(f"\n[{slice_num}/{num_intervals}] ({progress:.1f}%) ", end='')
                print(f"Executing {slice_quantity:.8f} {symbol} @ ${current_price:,.2f}")
                
                try:
                    if self.dry_run:
                        # Simulate order
                        order = {
                            'orderId': 9999000 + slice_num,
                            'symbol': symbol,
                            'side': side,
                            'type': 'LIMIT' if limit_price else 'MARKET',
                            'origQty': str(slice_quantity),
                            'executedQty': str(slice_quantity),
                            'avgPrice': str(current_price),
                            'status': 'FILLED'
                        }
                        time.sleep(0.5)  # Simulate execution delay
                    else:
                        # Execute actual order
                        if limit_price:
                            # Use limit orders
                            order = self.client.futures_create_order(
                                symbol=symbol,
                                side=side,
                                type='LIMIT',
                                quantity=slice_quantity,
                                price=limit_price,
                                timeInForce='IOC'  # Immediate or Cancel
                            )
                        else:
                            # Use market orders
                            order = self.client.futures_create_order(
                                symbol=symbol,
                                side=side,
                                type='MARKET',
                                quantity=slice_quantity
                            )
                    
                    self.executed_orders.append(order)
                    
                    # Log execution
                    BotLogger.log_order(
                        order_type='TWAP_SLICE',
                        symbol=symbol,
                        side=side,
                        quantity=slice_quantity,
                        price=current_price,
                        order_id=order['orderId'],
                        slice_number=slice_num,
                        total_slices=num_intervals
                    )
                    
                    executed_qty = float(order.get('executedQty', slice_quantity))
                    avg_price = float(order.get('avgPrice', current_price))
                    
                    print(f"    ✅ Filled: {executed_qty:.8f} @ ${avg_price:,.2f}")
                    
                except BinanceAPIException as e:
                    error_msg = f"Slice {slice_num} failed: {e.message}"
                    log_error(error_msg, e)
                    print(f"    ❌ Failed: {e.message}")
                    
                    if not self.dry_run:
                        confirm = input("Continue with remaining slices? (yes/no): ").strip().lower()
                        if confirm != 'yes':
                            break
                
                # Wait for next interval (except on last slice)
                if slice_num < num_intervals:
                    print(f"    ⏳ Waiting {interval_seconds:.1f}s for next slice...")
                    
                    # Progress bar for waiting
                    for j in range(int(interval_seconds)):
                        remaining = int(interval_seconds) - j
                        print(f"\r    ⏳ Next slice in {remaining}s...  ", end='', flush=True)
                        time.sleep(1)
                    print()  # New line after progress
            
            # Calculate execution summary
            total_executed = sum(float(o.get('executedQty', 0)) for o in self.executed_orders)
            total_cost = sum(float(o.get('executedQty', 0)) * float(o.get('avgPrice', 0)) 
                           for o in self.executed_orders)
            avg_execution_price = total_cost / total_executed if total_executed > 0 else 0
            
            # Display completion summary
            print("\n" + "="*60)
            print("TWAP EXECUTION COMPLETED")
            print("="*60)
            print(f"Slices Executed:      {len(self.executed_orders)}/{num_intervals}")
            print(f"Total Quantity:       {total_executed:.8f}")
            print(f"Average Price:        ${avg_execution_price:,.2f}")
            print(f"Total Value:          ${total_cost:,.2f} USDT")
            print(f"Price vs Start:       {((avg_execution_price - start_price) / start_price * 100):+.2f}%")
            print("="*60)
            
            # Log completion
            BotLogger.log_strategy(
                strategy_name='TWAP',
                action='Execution Completed',
                symbol=symbol,
                slices_executed=len(self.executed_orders),
                total_slices=num_intervals,
                total_quantity=total_executed,
                avg_price=avg_execution_price,
                total_cost=total_cost
            )
            
            return self.executed_orders
            
        except KeyboardInterrupt:
            log_info("TWAP execution interrupted by user")
            print("\n\n⚠️  Execution interrupted!")
            print(f"Executed {len(self.executed_orders)}/{num_intervals} slices")
            return self.executed_orders
            
        except Exception as e:
            error_msg = f"TWAP execution error: {str(e)}"
            log_error(error_msg, e)
            BotLogger.log_error('TWAP Error', error_msg, e,
                              symbol=symbol, side=side, total_quantity=total_quantity)
            return self.executed_orders
    
    def get_execution_summary(self) -> Dict:
        """
        Get summary of TWAP execution
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.executed_orders:
            return {}
        
        total_qty = sum(float(o.get('executedQty', 0)) for o in self.executed_orders)
        total_cost = sum(float(o.get('executedQty', 0)) * float(o.get('avgPrice', 0)) 
                        for o in self.executed_orders)
        avg_price = total_cost / total_qty if total_qty > 0 else 0
        
        prices = [float(o.get('avgPrice', 0)) for o in self.executed_orders]
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        return {
            'total_slices': len(self.executed_orders),
            'total_quantity': total_qty,
            'total_cost': total_cost,
            'average_price': avg_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_range': max_price - min_price
        }


def main():
    """Main entry point for TWAP strategy CLI"""
    parser = argparse.ArgumentParser(
        description='Execute TWAP (Time-Weighted Average Price) strategy on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute 0.01 BTC buy over 3 minutes in 3 slices (every 1 min)
  python twap.py BTCUSDT BUY 0.01 --duration 3 --intervals 3
  
  # Execute 0.1 ETH sell over 10 minutes in 5 slices (every 2 min)
  python twap.py ETHUSDT SELL 0.1 --duration 10 --intervals 5
  
  # Use limit orders at specific price
  python twap.py BTCUSDT BUY 0.01 --duration 3 --intervals 3 --limit-price 50000
  
  # Simulate without executing
  python twap.py BTCUSDT BUY 0.01 --duration 3 --intervals 3 --dry-run

Use Cases:
  - Execute large orders without moving the market
  - Minimize market impact and slippage
  - Achieve average execution price over time
  - Reduce exposure to short-term volatility
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('side', type=str, choices=['BUY', 'SELL', 'buy', 'sell'],
                       help='Order side')
    parser.add_argument('quantity', type=float, help='Total quantity to execute')
    parser.add_argument('--duration', '-d', type=int, required=True,
                       help='Total duration in minutes')
    parser.add_argument('--intervals', '-n', type=int, required=True,
                       help='Number of order slices')
    parser.add_argument('--limit-price', '-p', type=float,
                       help='Limit price for orders (default: market orders)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate execution without placing orders')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.intervals <= 0:
        print("\n❌ Error: intervals must be positive")
        sys.exit(1)
    
    if args.duration <= 0:
        print("\n❌ Error: duration must be positive")
        sys.exit(1)
    
    if args.quantity <= 0:
        print("\n❌ Error: quantity must be positive")
        sys.exit(1)
    
    # Print banner
    print_banner()
    
    # Create executor
    executor = TWAPExecutor(dry_run=args.dry_run)
    
    # Execute TWAP strategy
    orders = executor.execute_twap(
        symbol=args.symbol.upper(),
        side=args.side.upper(),
        total_quantity=args.quantity,
        duration_minutes=args.duration,
        num_intervals=args.intervals,
        limit_price=args.limit_price
    )
    
    if orders:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()