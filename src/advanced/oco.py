#!/usr/bin/env python3
"""
OCO (One-Cancels-the-Other) Orders Module
Places simultaneous take-profit and stop-loss orders
"""

import sys
import argparse
from typing import Dict, Optional, Tuple
from binance.exceptions import BinanceAPIException
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BinanceClientManager, print_banner
from validator import OrderValidator
from logger import BotLogger, log_info, log_error


class OCOOrderExecutor:
    """Handles OCO order execution on Binance Futures"""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize OCO order executor
        
        Args:
            dry_run: If True, simulate orders without executing
        """
        self.client = BinanceClientManager.get_client()
        self.dry_run = dry_run
        self.logger = BotLogger.get_logger()
    
    def place_oco_orders(self, symbol: str, side: str, quantity: float,
                        take_profit_price: float, stop_loss_price: float,
                        stop_limit_price: Optional[float] = None) -> Optional[Tuple[Dict, Dict]]:
        """
        Place OCO orders (take-profit limit + stop-loss stop-limit)
        
        When one order executes, the other is automatically cancelled.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: Order side for take-profit (BUY/SELL)
            quantity: Order quantity
            take_profit_price: Take-profit limit price
            stop_loss_price: Stop-loss trigger price
            stop_limit_price: Stop-loss limit price (optional, auto-calculated if None)
            
        Returns:
            Tuple of (take_profit_order, stop_loss_order) or None if failed
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
            
            # Validate and round take-profit price
            valid, msg, take_profit_price = OrderValidator.validate_price(symbol, take_profit_price)
            if not valid:
                log_error(f"Take-profit price validation failed: {msg}")
                return None
            
            # Validate and round stop-loss price
            valid, msg, stop_loss_price = OrderValidator.validate_price(symbol, stop_loss_price)
            if not valid:
                log_error(f"Stop-loss price validation failed: {msg}")
                return None
            
            # Calculate stop-limit price if not provided
            if stop_limit_price is None:
                # Set limit slightly worse than stop (0.1% offset)
                if side == 'SELL':
                    stop_limit_price = stop_loss_price * 0.999
                else:
                    stop_limit_price = stop_loss_price * 1.001
            
            # Validate and round stop-limit price
            valid, msg, stop_limit_price = OrderValidator.validate_price(symbol, stop_limit_price)
            if not valid:
                log_error(f"Stop-limit price validation failed: {msg}")
                return None
            
            # Get current price for reference
            current_price = OrderValidator.get_current_price(symbol)
            
            # Validate OCO logic
            if side == 'SELL':
                if take_profit_price <= current_price:
                    print(f"\n⚠️  Warning: Take-profit (${take_profit_price:,.2f}) should be above current price (${current_price:,.2f})")
                if stop_loss_price >= current_price:
                    print(f"\n⚠️  Warning: Stop-loss (${stop_loss_price:,.2f}) should be below current price (${current_price:,.2f})")
            else:
                if take_profit_price >= current_price:
                    print(f"\n⚠️  Warning: Take-profit (${take_profit_price:,.2f}) should be below current price (${current_price:,.2f})")
                if stop_loss_price <= current_price:
                    print(f"\n⚠️  Warning: Stop-loss (${stop_loss_price:,.2f}) should be above current price (${current_price:,.2f})")
            
            # Calculate profit/loss scenarios
            tp_value = abs((take_profit_price - current_price) * quantity)
            sl_value = abs((current_price - stop_loss_price) * quantity)
            risk_reward = tp_value / sl_value if sl_value > 0 else 0
            
            # Display order summary
            print("\n" + "="*60)
            print("OCO ORDER SUMMARY")
            print("="*60)
            print(f"Symbol:               {symbol}")
            print(f"Side:                 {side} (Exit Position)")
            print(f"Quantity:             {quantity}")
            print(f"Current Price:        ${current_price:,.2f}")
            print(f"\n📈 TAKE PROFIT:")
            print(f"  Price:              ${take_profit_price:,.2f}")
            print(f"  Potential Profit:   ${tp_value:,.2f} USDT")
            print(f"\n📉 STOP LOSS:")
            print(f"  Stop Price:         ${stop_loss_price:,.2f}")
            print(f"  Limit Price:        ${stop_limit_price:,.2f}")
            print(f"  Potential Loss:     ${sl_value:,.2f} USDT")
            print(f"\n⚖️  Risk/Reward Ratio:  {risk_reward:.2f}")
            print(f"Mode:                 {'DRY RUN' if self.dry_run else 'LIVE'}")
            print("="*60)
            
            if risk_reward < 1.0:
                print("\n⚠️  WARNING: Risk/Reward ratio is below 1:1")
                print("    Consider adjusting your take-profit or stop-loss levels")
            
            # Confirmation for live orders
            if not self.dry_run:
                confirm = input("\nConfirm OCO order placement? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    log_info("OCO order cancelled by user")
                    return None
            
            if self.dry_run:
                # Simulate orders
                log_info("DRY RUN: OCO orders simulated successfully")
                
                tp_order = {
                    'orderId': 9999998,
                    'symbol': symbol,
                    'side': side,
                    'type': 'LIMIT',
                    'origQty': str(quantity),
                    'price': str(take_profit_price),
                    'status': 'NEW'
                }
                
                sl_order = {
                    'orderId': 9999999,
                    'symbol': symbol,
                    'side': side,
                    'type': 'STOP',
                    'origQty': str(quantity),
                    'stopPrice': str(stop_loss_price),
                    'price': str(stop_limit_price),
                    'status': 'NEW'
                }
                
                return (tp_order, sl_order)
            
            # Place actual orders
            log_info(f"Placing OCO orders for {symbol}")
            
            # Place take-profit limit order
            log_info(f"Placing take-profit limit: {side} {quantity} @ ${take_profit_price}")
            tp_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=take_profit_price,
                timeInForce='GTC',
                reduceOnly=True
            )
            
            BotLogger.log_order(
                order_type='TAKE_PROFIT',
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=take_profit_price,
                order_id=tp_order['orderId'],
                oco_type='take_profit'
            )
            
            # Small delay
            time.sleep(0.5)
            
            # Place stop-loss stop-limit order
            log_info(f"Placing stop-loss: {side} {quantity} stop=${stop_loss_price} limit=${stop_limit_price}")
            sl_order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP',
                quantity=quantity,
                price=stop_limit_price,
                stopPrice=stop_loss_price,
                timeInForce='GTC',
                reduceOnly=True
            )
            
            BotLogger.log_order(
                order_type='STOP_LOSS',
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=stop_limit_price,
                stop_price=stop_loss_price,
                order_id=sl_order['orderId'],
                oco_type='stop_loss'
            )
            
            # Log OCO relationship
            BotLogger.log_strategy(
                strategy_name='OCO',
                action='Orders Placed',
                tp_order_id=tp_order['orderId'],
                sl_order_id=sl_order['orderId'],
                symbol=symbol,
                quantity=quantity
            )
            
            # Display success
            print("\n" + "="*60)
            print("OCO ORDERS PLACED SUCCESSFULLY")
            print("="*60)
            print(f"Take-Profit Order ID: {tp_order['orderId']}")
            print(f"Stop-Loss Order ID:   {sl_order['orderId']}")
            print("="*60)
            print("\n💡 When one order executes, manually cancel the other")
            print("⚠️  NOTE: Binance Futures doesn't have native OCO,")
            print("    so orders must be managed manually or with a bot")
            
            return (tp_order, sl_order)
            
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


def main():
    """Main entry point for OCO order CLI"""
    parser = argparse.ArgumentParser(
        description='Execute OCO (One-Cancels-the-Other) orders on Binance Futures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Close long position with TP at $52k and SL at $49k
  python oco.py BTCUSDT SELL 0.001 52000 49000 48900
  
  # Auto-calculate stop-limit price
  python oco.py BTCUSDT SELL 0.001 52000 49000
  
  # Simulate without executing
  python oco.py BTCUSDT SELL 0.001 52000 49000 --dry-run
        """
    )
    
    parser.add_argument('symbol', type=str, help='Trading pair (e.g., BTCUSDT)')
    parser.add_argument('side', type=str, choices=['BUY', 'SELL', 'buy', 'sell'],
                       help='Order side (for exit)')
    parser.add_argument('quantity', type=float, help='Order quantity')
    parser.add_argument('take_profit_price', type=float, help='Take-profit price')
    parser.add_argument('stop_loss_price', type=float, help='Stop-loss trigger price')
    parser.add_argument('stop_limit_price', type=float, nargs='?',
                       help='Stop-loss limit price (optional)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate orders without executing')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Create executor
    executor = OCOOrderExecutor(dry_run=args.dry_run)
    
    # Execute OCO orders
    orders = executor.place_oco_orders(
        symbol=args.symbol.upper(),
        side=args.side.upper(),
        quantity=args.quantity,
        take_profit_price=args.take_profit_price,
        stop_loss_price=args.stop_loss_price,
        stop_limit_price=args.stop_limit_price
    )
    
    if orders:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()