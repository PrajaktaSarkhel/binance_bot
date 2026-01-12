#!/usr/bin/env python3
"""
Grid Trading Strategy Module
Automated buy-low/sell-high within a price range
"""

import sys
import argparse
import time
from typing import Dict, List, Optional
from datetime import datetime
from binance.exceptions import BinanceAPIException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class GridTradingStrategy:
    """Implements grid trading strategy on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize grid trading strategy
        
        Args:
            dry_run: If True, simulate orders without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
        self.grid_levels = []
        self.active_orders = []
        self.filled_orders = []
        self.total_profit = 0.0
    
    def calculate_grid_levels(self, lower_price: float, upper_price: float,
                            num_grids: int) -> List[float]:
        """
        Calculate grid price levels
        
        Args:
            lower_price: Lower bound of price range
            upper_price: Upper bound of price range
            num_grids: Number of grid levels
            
        Returns:
            List of grid price levels
        """
        price_range = upper_price - lower_price
        grid_step = price_range / num_grids
        
        levels = [lower_price + (i * grid_step) for i in range(num_grids + 1)]
        return levels
    
    def setup_grid(self, symbol: str, lower_price: float, upper_price: float,
                   num_grids: int, quantity_per_grid: float) -> bool:
        """
        Set up initial grid orders
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            lower_price: Lower bound of price range
            upper_price: Upper bound of price range
            num_grids: Number of grid levels
            quantity_per_grid: Quantity for each grid level
            
        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Validate parameters
            valid, msg = OrderValidator.validate_symbol(symbol)
            if not valid:
                log_error(f"Validation failed: {msg}")
                return False
            
            # Validate prices
            valid, msg, lower_price = OrderValidator.validate_price(symbol, lower_price)
            if not valid:
                log_error(f"Lower price validation failed: {msg}")
                return False
            
            valid, msg, upper_price = OrderValidator.validate_price(symbol, upper_price)
            if not valid:
                log_error(f"Upper price validation failed: {msg}")
                return False
            
            # Validate quantity
            valid, msg, quantity_per_grid = OrderValidator.validate_quantity(symbol, quantity_per_grid)
            if not valid:
                log_error(f"Quantity validation failed: {msg}")
                return False
            
            if lower_price >= upper_price:
                log_error("Lower price must be less than upper price")
                return False
            
            # Calculate grid levels
            self.grid_levels = self.calculate_grid_levels(lower_price, upper_price, num_grids)
            
            # Get current price
            current_price = OrderValidator.get_current_price(symbol)
            
            # Calculate total investment
            total_investment = 0
            buy_orders_count = 0
            sell_orders_count = 0
            
            for level in self.grid_levels:
                if level < current_price:
                    buy_orders_count += 1
                    total_investment += level * quantity_per_grid
                elif level > current_price:
                    sell_orders_count += 1
            
            # Display grid summary
            print("\n" + "="*60)
            print("GRID TRADING STRATEGY SUMMARY")
            print("="*60)
            print(f"Symbol:               {symbol}")
            print(f"Price Range:          ${lower_price:,.2f} - ${upper_price:,.2f}")
            print(f"Current Price:        ${current_price:,.2f}")
            print(f"Grid Levels:          {len(self.grid_levels)}")
            print(f"Quantity per Level:   {quantity_per_grid}")
            print(f"Grid Step:            ${(upper_price - lower_price) / num_grids:,.2f}")
            print(f"\nOrder Distribution:")
            print(f"  Buy Orders:         {buy_orders_count} (below current price)")
            print(f"  Sell Orders:        {sell_orders_count} (above current price)")
            print(f"  Total Investment:   ${total_investment:,.2f} USDT")
            print(f"\nMode:                 {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
            # Display grid levels
            print("\nGrid Levels:")
            for i, level in enumerate(self.grid_levels, 1):
                marker = "🔵" if level < current_price else "🔴" if level > current_price else "⚪"
                order_type = "BUY" if level < current_price else "SELL" if level > current_price else "CURRENT"
                print(f"  {marker} Level {i:2d}: ${level:,.2f} ({order_type})")
            
            # Check if current price is within range
            if current_price < lower_price or current_price > upper_price:
                print(f"\n⚠️  WARNING: Current price (${current_price:,.2f}) is outside grid range!")
                print("    Grid will only trigger when price returns to range.")
            
            # Confirmation for live orders
            if not self.dry_run:
                confirm = input("\nConfirm grid setup? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    log_info("Grid setup cancelled by user")
                    return False
            
            # Place grid orders
            print("\n" + "="*60)
            print("PLACING GRID ORDERS")
            print("="*60)
            
            for i, level in enumerate(self.grid_levels, 1):
                # Skip level at current price
                if abs(level - current_price) / current_price < 0.001:  # Within 0.1%
                    print(f"[{i}/{len(self.grid_levels)}] Skipping level at current price: ${level:,.2f}")
                    continue
                
                # Determine order side
                side = 'BUY' if level < current_price else 'SELL'
                
                print(f"[{i}/{len(self.grid_levels)}] Placing {side} order at ${level:,.2f}...", end=' ')
                
                try:
                    if self.dry_run:
                        # Simulate order
                        order = {
                            'orderId': 8888000 + i,
                            'symbol': symbol,
                            'side': side,
                            'type': 'LIMIT',
                            'origQty': str(quantity_per_grid),
                            'price': str(level),
                            'status': 'NEW'
                        }
                        time.sleep(0.1)
                    else:
                        # Place actual limit order
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=side,
                            type='LIMIT',
                            quantity=quantity_per_grid,
                            price=level,
                            timeInForce='GTC'
                        )
                    
                    self.active_orders.append(order)
                    
                    # Log order
                    BotLogger.log_order(
                        order_type='GRID',
                        symbol=symbol,
                        side=side,
                        quantity=quantity_per_grid,
                        price=level,
                        order_id=order['orderId'],
                        grid_level=i
                    )
                    
                    print(f"✅ Order ID: {order['orderId']}")
                    
                except BinanceAPIException as e:
                    print(f"❌ Failed: {e.message}")
                    log_error(f"Failed to place grid order at ${level}: {e.message}", e)
            
            # Log grid setup
            BotLogger.log_strategy(
                strategy_name='Grid Trading',
                action='Grid Setup Complete',
                symbol=symbol,
                grid_levels=len(self.grid_levels),
                active_orders=len(self.active_orders),
                lower_price=lower_price,
                upper_price=upper_price
            )
            
            print("\n" + "="*60)
            print("GRID SETUP COMPLETE")
            print("="*60)
            print(f"Active Orders:        {len(self.active_orders)}")
            print("="*60)
            
            return True
            
        except Exception as e:
            error_msg = f"Grid setup error: {str(e)}"
            log_error(error_msg, e)
            BotLogger.log_error('Grid Setup Error', error_msg, e,
                              symbol=symbol, lower_price=lower_price, upper_price=upper_price)
            return False
    
    def monitor_grid(self, symbol: str, quantity_per_grid: float,
                    check_interval: int = 5) -> None:
        """
        Monitor and maintain grid orders
        
        Args:
            symbol: Trading pair
            quantity_per_grid: Quantity for replacement orders
            check_interval: Seconds between checks
        """
        log_info(f"Starting grid monitoring for {symbol}")
        print("\n" + "="*60)
        print("MONITORING GRID")
        print("="*60)
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                
                # Check all active orders
                filled_this_round = []
                
                for order in self.active_orders[:]:  # Create a copy to iterate
                    try:
                        # Check order status
                        order_status = self.client.futures_get_order(
                            symbol=symbol,
                            orderId=order['orderId']
                        )
                        
                        if order_status['status'] == 'FILLED':
                            filled_this_round.append(order)
                            self.active_orders.remove(order)
                            self.filled_orders.append(order_status)
                            
                            # Calculate profit (simplified)
                            executed_qty = float(order_status['executedQty'])
                            avg_price = float(order_status['avgPrice'])
                            side = order_status['side']
                            
                            # Log execution
                            print(f"\n[{current_time}] ✅ Order filled!")
                            print(f"  {side} {executed_qty} @ ${avg_price:,.2f}")
                            print(f"  Order ID: {order['orderId']}")
                            
                            BotLogger.log_execution(
                                order_id=order['orderId'],
                                symbol=symbol,
                                side=side,
                                executed_qty=executed_qty,
                                avg_price=avg_price,
                                status='FILLED'
                            )
                            
                            # Place replacement order on opposite side
                            if not self.dry_run:
                                self._place_replacement_order(
                                    symbol, side, avg_price, 
                                    quantity_per_grid
                                )
                    
                    except Exception as e:
                        log_error(f"Error checking order {order['orderId']}: {str(e)}", e)
                
                # Display status
                if iteration % 6 == 0:  # Every 30 seconds if check_interval=5
                    current_price = OrderValidator.get_current_price(symbol)
                    print(f"\n[{current_time}] Status Update:")
                    print(f"  Current Price:    ${current_price:,.2f}")
                    print(f"  Active Orders:    {len(self.active_orders)}")
                    print(f"  Filled Orders:    {len(self.filled_orders)}")
                    print(f"  Total Profit:     ${self.total_profit:,.2f} USDT")
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped by user")
            self._display_final_stats(symbol)
        except Exception as e:
            log_error(f"Error in grid monitoring: {str(e)}", e)
            self._display_final_stats(symbol)
    
    def _place_replacement_order(self, symbol: str, filled_side: str,
                                filled_price: float, quantity: float) -> None:
        """Place replacement order after a grid order is filled"""
        try:
            # Opposite side
            new_side = 'SELL' if filled_side == 'BUY' else 'BUY'
            
            # Calculate new price (slightly profitable)
            grid_step = (self.grid_levels[1] - self.grid_levels[0]) if len(self.grid_levels) > 1 else filled_price * 0.01
            
            if new_side == 'SELL':
                new_price = filled_price + grid_step
            else:
                new_price = filled_price - grid_step
            
            # Validate and round price
            valid, msg, new_price = OrderValidator.validate_price(symbol, new_price)
            if not valid:
                log_error(f"Replacement order price validation failed: {msg}")
                return
            
            print(f"\n  📌 Placing replacement {new_side} order at ${new_price:,.2f}")
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=new_side,
                type='LIMIT',
                quantity=quantity,
                price=new_price,
                timeInForce='GTC'
            )
            
            self.active_orders.append(order)
            
            BotLogger.log_order(
                order_type='GRID_REPLACEMENT',
                symbol=symbol,
                side=new_side,
                quantity=quantity,
                price=new_price,
                order_id=order['orderId']
            )
            
            print(f"  ✅ Replacement order placed: ID {order['orderId']}")
            
        except Exception as e:
            log_error(f"Failed to place replacement order: {str(e)}", e)
    
    def _display_final_stats(self, symbol: str) -> None:
        """Display final grid trading statistics"""
        print("\n" + "="*60)
        print("GRID TRADING FINAL STATISTICS")
        print("="*60)
        print(f"Symbol:               {symbol}")
        print(f"Total Orders Placed:  {len(self.active_orders) + len(self.filled_orders)}")
        print(f"Orders Filled:        {len(self.filled_orders)}")
        print(f"Orders Active:        {len(self.active_orders)}")
        print(f"Estimated Profit:     ${self.total_profit:,.2f} USDT")
        print("="*60)
        
        BotLogger.log_strategy(
            strategy_name='Grid Trading',
            action='Monitoring Stopped',
            symbol=symbol,
            filled_orders=len(self.filled_orders),
            active_orders=len(self.active_orders),
            total_profit=self.total_profit
        )


def main():
    """Main entry point for grid trading strategy CLI"""
    parser = argparse.ArgumentParser(
        description='Execute grid trading strategy on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set up grid between $48k-$52k with 10 levels, 0.01 BTC each
  python grid_strategy.py BTCUSDT 48000 52000 10 0.01
  
  # Set up and monitor grid
  python grid_strategy.py BTCUSDT 48000 52000 10 0.01 --monitor
  
  # Custom check interval (10 seconds)
  python grid_strategy.py BTCUSDT 48000 52000 10 0.01 --monitor --interval 10
  
  # Simulate without executing
  python grid_strategy.py BTCUSDT 48000 52000 10 0.01 --dry-run

Use Cases:
  - Profit from ranging/sideways markets
  - Automated buy-low/sell-high strategy
  - Generate income in consolidation zones
  - Reduce need for market timing
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('lower_price', type=float, help='Lower bound of price range')
    parser.add_argument('upper_price', type=float, help='Upper bound of price range')
    parser.add_argument('num_grids', type=int, help='Number of grid levels')
    parser.add_argument('quantity_per_grid', type=float, help='Quantity per grid level')
    parser.add_argument('--monitor', '-m', action='store_true',
                       help='Monitor and maintain grid after setup')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='Check interval in seconds (default: 5)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate without placing orders')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Validate parameters
    if args.num_grids <= 0:
        print("\n❌ Error: num_grids must be positive")
        sys.exit(1)
    
    if args.lower_price >= args.upper_price:
        print("\n❌ Error: lower_price must be less than upper_price")
        sys.exit(1)
    
    # Print banner
    print_banner()
    
    # Create strategy
    strategy = GridTradingStrategy(dry_run=args.dry_run)
    
    # Set up grid
    success = strategy.setup_grid(
        symbol=args.symbol.upper(),
        lower_price=args.lower_price,
        upper_price=args.upper_price,
        num_grids=args.num_grids,
        quantity_per_grid=args.quantity_per_grid
    )
    
    if not success:
        sys.exit(1)
    
    # Monitor if requested
    if args.monitor and not args.dry_run:
        strategy.monitor_grid(
            symbol=args.symbol.upper(),
            quantity_per_grid=args.quantity_per_grid,
            check_interval=args.interval
        )
    elif args.monitor and args.dry_run:
        print("\n💡 Monitoring is not available in dry-run mode")
    
    sys.exit(0)


if __name__ == "__main__":
    main()