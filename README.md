# Binance Futures Trading Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures that supports multiple order types including market, limit, and advanced orders (Stop-Limit, OCO, TWAP, and Grid trading).

## ✨ Features

### Core Orders
- **Market Orders**: Execute instant buy/sell orders at current market price
- **Limit Orders**: Place orders at specific price levels

### Advanced Orders
- **Stop-Limit Orders**: Trigger limit orders when a stop price is reached
- **OCO (One-Cancels-the-Other)**: Simultaneously place take-profit and stop-loss orders
- **TWAP (Time-Weighted Average Price)**: Split large orders into smaller chunks over time
- **Grid Trading**: Automated buy-low/sell-high strategy within a defined price range

### Additional Features
- Comprehensive input validation (symbol, quantity, price thresholds)
- Structured logging with timestamps and error traces
- Position management and monitoring
- Real-time order status tracking
- Testnet support for safe testing

## 📁 Project Structure

```
binance_bot/
│
├── src/
│   ├── market_orders.py          # Market order execution
│   ├── limit_orders.py            # Limit order placement
│   ├── config.py                  # Configuration management
│   ├── logger.py                  # Logging setup
│   ├── validator.py               # Input validation
│   ├── utils.py                   # Helper functions
│   │
│   └── advanced/
│       ├── stop_limit.py          # Stop-limit order logic
│       ├── oco.py                 # OCO order implementation
│       ├── twap.py                # TWAP strategy
│       └── grid_strategy.py       # Grid trading bot
│
├── tests/
│   ├── test_market_orders.py
│   ├── test_limit_orders.py
│   └── test_advanced_orders.py
│
├── bot.log                        # Execution logs
├── .env.example                   # Environment variables template
├── .gitignore
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── report.pdf                     # Analysis and screenshots
```

## 🔧 Prerequisites

- Python 3.8 or higher
- Binance account with Futures trading enabled
- API keys with Futures trading permissions

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PrajaktaSarkhel/binance_bot.git
   cd binance_bot
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🔑 API Setup

### Step 1: Create Binance API Keys

1. Log in to your [Binance account](https://www.binance.com/)
2. Navigate to **API Management** (Profile → API Management)
3. Click **Create API** and complete security verification
4. **Important**: Enable the following permissions:
   - ✅ Enable Futures
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading (if needed)
5. **Save your API Key and Secret Key** securely

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   # Binance API Credentials
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_secret_key_here
   
   # Use testnet for safe testing (recommended)
   USE_TESTNET=True
   
   # Testnet credentials (if using testnet)
   TESTNET_API_KEY=your_testnet_api_key
   TESTNET_API_SECRET=your_testnet_secret_key
   ```

### Step 3: Testnet Setup (Recommended for Testing)

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Create a testnet account
3. Generate testnet API keys
4. Use testnet credentials in your `.env` file

⚠️ **Security Warning**: Never commit your `.env` file or expose your API keys publicly!

## ⚙️ Configuration

Edit `src/config.py` to customize bot behavior:

- Order parameters (default quantities, leverage, etc.)
- Risk management settings
- Logging preferences
- API endpoints

## 🚀 Usage

### Market Orders

Execute a market order:

```bash
# Buy market order
python src/market_orders.py BTCUSDT BUY 0.01

# Sell market order
python src/market_orders.py ETHUSDT SELL 0.1
```

### Limit Orders

Place a limit order at a specific price:

```bash
# Buy limit order
python src/limit_orders.py BTCUSDT BUY 0.01 45000.00

# Sell limit order
python src/limit_orders.py ETHUSDT SELL 0.1 3500.00
```

### Advanced Orders

#### Stop-Limit Orders

Trigger a limit order when price hits stop price:

```bash
python src/advanced/stop_limit.py BTCUSDT BUY 0.01 --stop-price 44000 --limit-price 44100
```

#### OCO Orders

Place take-profit and stop-loss simultaneously:

```bash
python src/advanced/oco.py BTCUSDT SELL 0.01 --take-profit 46000 --stop-loss 43000
```

#### TWAP Strategy

Split large orders over time:

```bash
python src/advanced/twap.py BTCUSDT BUY 1.0 --duration 3600 --intervals 12
```

#### Grid Trading

Automated buy-low/sell-high within price range:

```bash
python src/advanced/grid_strategy.py BTCUSDT 40000 50000 10 0.01
```

## 📊 Order Types Explained

### Market Orders
Execute immediately at the best available market price. Use for quick entries/exits when price is secondary to speed.

### Limit Orders
Place orders at specific price levels. The order will only execute if the market reaches your specified price.

### Stop-Limit Orders
Two-step process: When the market hits your stop price, a limit order is triggered at your specified limit price. Useful for limiting losses or entering breakouts.

### OCO (One-Cancels-the-Other)
Place two orders simultaneously (typically take-profit and stop-loss). When one executes, the other is automatically cancelled.

### TWAP (Time-Weighted Average Price)
Split large orders into smaller chunks executed at regular intervals. Reduces market impact and achieves average pricing over time.

### Grid Trading
Automatically place buy and sell orders at predetermined price levels within a range. Profits from price oscillations in ranging markets.

## 📝 Logging

All bot activities are logged in `bot.log` with the following structure:

```
2025-01-12 10:30:45 - INFO - Market order placed: BTCUSDT BUY 0.01
2025-01-12 10:30:46 - SUCCESS - Order executed: Order ID 123456789
2025-01-12 10:35:22 - ERROR - Invalid symbol: INVALID_SYMBOL
2025-01-12 10:40:10 - WARNING - Low account balance detected
```

Logs include:
- Timestamps for all actions
- Order placements and executions
- API responses and errors
- Validation failures
- System warnings

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_market_orders.py

# Run with verbose output
python -m pytest -v tests/
```

**Important**: Always test on Binance Testnet before using real funds!

## ⚠️ Error Handling

The bot implements comprehensive error handling for:

- **Invalid Symbols**: Validates trading pairs against Binance exchange info
- **Insufficient Balance**: Checks account balance before order placement
- **Price Validation**: Ensures prices meet minimum tick size requirements
- **Quantity Validation**: Verifies quantities meet minimum order size
- **API Errors**: Handles rate limits, network errors, and authentication failures
- **Order Failures**: Logs and reports failed orders with detailed error messages

## 📋 Requirements

Main dependencies (see `requirements.txt` for complete list):

```
python-binance>=1.0.17
python-dotenv>=1.0.0
requests>=2.31.0
pandas>=2.0.0
pytest>=7.4.0
```

## 🛡️ Risk Management

**Trading involves significant risk. Please consider the following:**

- Start with small amounts and use testnet first
- Never invest more than you can afford to lose
- Use stop-loss orders to limit potential losses
- Monitor your positions regularly
- Understand leverage risks in futures trading
- Keep your API keys secure and use IP whitelisting

## 📄 Documentation

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Project Report](report.pdf) - Detailed analysis with screenshots and explanations
- Check `bot.log` for execution history

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

Prajakta Sarkhel - [GitHub](https://github.com/PrajaktaSarkhel)

Project Link: [https://github.com/PrajaktaSarkhel/binance_bot](https://github.com/PrajaktaSarkhel/binance_bot)

## ⚖️ Disclaimer

**THIS SOFTWARE IS FOR EDUCATIONAL PURPOSES ONLY.**

This trading bot is provided as-is without any guarantees or warranty. The authors are not responsible for any financial losses incurred through the use of this software. Cryptocurrency trading carries substantial risk of loss and is not suitable for all investors. Always do your own research and consult with a financial advisor before trading.

By using this bot, you acknowledge that:
- You are solely responsible for your trading decisions
- Past performance does not guarantee future results
- You understand the risks involved in cryptocurrency futures trading
- You will comply with all applicable laws and regulations

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**⭐ If you find this project helpful, please consider giving it a star!**
