"""
Configuration module for Binance Futures Trading Bot
Handles API credentials, client initialization, and global settings
"""

import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the trading bot"""
    
    # API Configuration
    API_KEY = os.getenv('BINANCE_API_KEY', '')
    API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    TESTNET = os.getenv('TESTNET', 'True').lower() == 'true'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'bot.log'
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Trading Configuration
    DEFAULT_RECV_WINDOW = 5000  # milliseconds
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1  # seconds
    
    # Safety Limits
    MAX_ORDER_VALUE_USD = 10000  # Maximum single order value
    MIN_ORDER_VALUE_USD = 10     # Minimum order value
    
    # Testnet URLs
    TESTNET_BASE_URL = 'https://testnet.binancefuture.com'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.API_KEY or not cls.API_SECRET:
            raise ValueError("API_KEY and API_SECRET must be set in .env file")
        return True


class BinanceClientManager:
    """Manages Binance client instances"""
    
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls, testnet: bool = None) -> Client:
        """
        Get or create Binance client instance
        
        Args:
            testnet: Override default testnet setting
            
        Returns:
            Binance Client instance
        """
        if cls._client is None:
            Config.validate()
            
            use_testnet = testnet if testnet is not None else Config.TESTNET
            
            if use_testnet:
                cls._client = Client(
                    Config.API_KEY,
                    Config.API_SECRET,
                    testnet=True
                )
                cls._client.API_URL = Config.TESTNET_BASE_URL
                print("⚠️  Using TESTNET - No real funds at risk")
            else:
                cls._client = Client(
                    Config.API_KEY,
                    Config.API_SECRET
                )
                print("⚠️  Using MAINNET - Real funds at risk!")
        
        return cls._client
    
    @classmethod
    def test_connection(cls) -> bool:
        """
        Test API connection and credentials
        
        Returns:
            True if connection successful
        """
        try:
            client = cls.get_client()
            client.futures_ping()
            account = client.futures_account()
            print(f"✅ Connected successfully")
            print(f"Account Balance: {account.get('totalWalletBalance', 'N/A')} USDT")
            return True
        except BinanceAPIException as e:
            print(f"❌ API Error: {e.message}")
            return False
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
            return False
    
    @classmethod
    def get_account_info(cls) -> dict:
        """Get futures account information"""
        client = cls.get_client()
        return client.futures_account()
    
    @classmethod
    def get_balance(cls, asset: str = 'USDT') -> float:
        """
        Get balance for specific asset
        
        Args:
            asset: Asset symbol (default: USDT)
            
        Returns:
            Available balance
        """
        client = cls.get_client()
        account = client.futures_account()
        
        for balance in account['assets']:
            if balance['asset'] == asset:
                return float(balance['availableBalance'])
        
        return 0.0
    
    @classmethod
    def get_position(cls, symbol: str) -> dict:
        """
        Get current position for symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Position information
        """
        client = cls.get_client()
        positions = client.futures_position_information(symbol=symbol)
        
        if positions:
            return positions[0]
        
        return {}


def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║     Binance Futures Trading Bot v1.0               ║
    ║     Educational Purpose Only - Use at Your Risk     ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)


if __name__ == "__main__":
    # Test configuration
    print_banner()
    print("\n🔍 Testing Configuration...\n")
    
    try:
        Config.validate()
        print("✅ Configuration valid")
        
        print("\n🔍 Testing API Connection...\n")
        BinanceClientManager.test_connection()
        
        print("\n💰 Account Balance:")
        balance = BinanceClientManager.get_balance()
        print(f"Available USDT: {balance}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPlease check your .env file and API credentials.")