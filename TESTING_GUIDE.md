# Testing Guide - Binance Futures Trading Bot

## 🎯 Testing Strategy

This guide will help you test all features of your trading bot systematically.

## 🔧 Setup for Testing

### 1. Get Testnet Credentials

1. Visit: https://testnet.binancefuture.com
2. Log in with GitHub or Google
3. Go to API Management
4. Generate API Key and Secret
5. Copy credentials to your `.env` file

### 2. Configure Environment

```bash
# .env file
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
TESTNET=True
LOG_LEVEL=INFO
```

### 3. Get Testnet Funds

- Testnet provides virtual USDT (fake money)
- No risk involved
- Reset balance if needed from testnet website

## ✅ Test Checklist

### Phase 1: Configuration & Connection (5 minutes)

**Test: API Connection**
```bash
python src/config.py
```

**Expected Output:**
- ✅ Configuration valid
- ✅ Connected successfully
- ✅ Account balance displayed

**Screenshots to Take:**
- Connection success message
- Account balance

---

### Phase 2: Core Orders Testing (15 minutes)

#### Test 2.1: Market Order (Buy)

```bash
# Dry run first
python src/market_orders.py BTCUSDT BUY 0.001 --dry-run

# Live on testnet
python src/market_orders.py BTCUSDT BUY 0.001
```

**Expected Output:**
- Order summary displayed
- Current price shown
- Confirmation prompt
- Order executed successfully
- Execution details shown

**Screenshots to Take:**
- Order summary
- Execution confirmation
- bot.log entry

**Verify in bot.log:**
```
INFO - Market order placed: BTCUSDT BUY 0.001
INFO - Order executed: BTCUSDT BUY 0.001 @ 50000.00 - Status: FILLED
```

#### Test 2.2: Market Order (Sell)

```bash
python src/market_orders.py BTCUSDT SELL 0.001
```

**Test both:**
- Successful execution
- Position closing

#### Test 2.3: Limit Order (Buy)

```bash
# Set price below current market (will wait for fill)
python src/limit_orders.py BTCUSDT BUY 0.001 45000

# Set price at/above current (should fill quickly)
python src/limit_orders.py BTCUSDT BUY 0.001 51000
```

**Expected Output:**
- Order placed successfully
- Order ID received
- Status: NEW or FILLED

**Screenshots to Take:**
- Order placement
- Order details

#### Test 2.4: Limit Order (Sell)

```bash
# Set price above current market
python src/limit_orders.py BTCUSDT SELL 0.001 55000
```

---

### Phase 3: Advanced Orders Testing (30 minutes)

#### Test 3.1: Stop-Limit Order

**Stop-Loss Test:**
```bash
# Current price: ~50000
# Stop at 49000, limit at 48900
python src/advanced/stop_limit.py BTCUSDT SELL 0.001 49000 48900 --dry-run

# Live test
python src/advanced/stop_limit.py BTCUSDT SELL 0.001 49000 48900
```

**Expected Output:**
- Stop-limit order summary
- Warning if price is too close
- Order placed with status NEW
- Will trigger when price reaches stop

**Stop-Buy Test:**
```bash
# Stop at 51000, limit at 51100
python src/advanced/stop_limit.py BTCUSDT BUY 0.001 51000 51100
```

**Screenshots to Take:**
- Order summary with warnings
- Order placement confirmation

#### Test 3.2: OCO Orders

```bash
# For a long position, set TP above and SL below
python src/advanced/oco.py BTCUSDT SELL 0.001 52000 49000 48900 --dry-run

# Live test
python src/advanced/oco.py BTCUSDT SELL 0.001 52000 49000 48900
```

**Expected Output:**
- OCO order summary
- Risk/reward ratio calculated
- Both orders placed successfully
- Two order IDs received

**Screenshots to Take:**
- Order summary with R/R ratio
- Both order confirmations
- Note about manual cancellation

**Test Monitoring (Optional):**
```bash
# Monitor OCO orders
python src/advanced/oco.py BTCUSDT --monitor --tp-id 12345 --sl-id 12346
```

#### Test 3.3: TWAP Strategy

**Quick Test (3 minutes):**
```bash
# Split 0.01 BTC over 3 minutes, 3 slices
python src/advanced/twap.py BTCUSDT BUY 0.01 --duration 3 --intervals 3 --dry-run

# Live test
python src/advanced/twap.py BTCUSDT BUY 0.01 --duration 3 --intervals 3
```

**Expected Output:**
- TWAP summary
- Estimated completion time
- Progress for each slice
- Countdown timer between slices
- Execution summary with average price

**Screenshots to Take:**
- TWAP summary
- Progress during execution
- Final execution summary

**Longer Test (Optional):**
```bash
# More realistic TWAP over 10 minutes
python src/advanced/twap.py BTCUSDT BUY 0.05 --duration 10 --intervals 5
```

#### Test 3.4: Grid Trading

**Setup Grid:**
```bash
# Grid between 48000-52000, 5 levels, 0.001 BTC each
python src/advanced/grid_strategy.py BTCUSDT 48000 52000 5 0.001 --dry-run

# Live test (without monitoring)
python src/advanced/grid_strategy.py BTCUSDT 48000 52000 5 0.001
```

**Expected Output:**
- Grid summary
- Grid levels displayed
- Order distribution (buy/sell)
- Each order placement confirmed

**Screenshots to Take:**
- Grid summary
- Grid levels visualization
- Setup completion

**Monitor Grid (Optional - Can run for longer):**
```bash
python src/advanced/grid_strategy.py BTCUSDT 48000 52000 5 0.001 --monitor
```

---

### Phase 4: Validation & Error Handling (10 minutes)

#### Test 4.1: Invalid Symbol
```bash
python src/market_orders.py INVALID BUY 0.01
```

**Expected:** Error message about invalid symbol

#### Test 4.2: Invalid Quantity
```bash
python src/market_orders.py BTCUSDT BUY 0.0000001
```

**Expected:** Error about minimum quantity

#### Test 4.3: Invalid Price
```bash
python src/limit_orders.py BTCUSDT BUY 0.01 0.01
```

**Expected:** Error about minimum price or notional value

#### Test 4.4: Insufficient Balance
```bash
python src/market_orders.py BTCUSDT BUY 1000
```

**Expected:** API error about insufficient balance

---

### Phase 5: Logging Verification (5 minutes)

**Check bot.log:**
```bash
cat bot.log
# or
tail -f bot.log  # Follow in real-time
```

**Verify Log Contains:**
- Timestamps for all operations
- Order placements
- Order executions
- Validation results
- Error messages with traces
- Strategy actions

**Example Good Log Entry:**
```
2025-01-10 15:30:45,123 - INFO - Market order placed: BTCUSDT BUY 0.01 - OrderID: 12345678
2025-01-10 15:30:45,456 - INFO - Order executed: BTCUSDT BUY 0.01 @ 50123.45 - Status: FILLED
2025-01-10 15:31:12,789 - INFO - Strategy [TWAP]: Executing slice 1/10
```

---

## 📸 Screenshot Checklist for Report

### Must-Have Screenshots (Minimum 15)

1. ✅ API connection success
2. ✅ Market order - dry run
3. ✅ Market order - live execution
4. ✅ Limit order placement
5. ✅ Stop-limit order summary
6. ✅ OCO order with R/R ratio
7. ✅ TWAP execution in progress
8. ✅ TWAP completion summary
9. ✅ Grid strategy setup
10. ✅ Grid levels visualization
11. ✅ bot.log samples (multiple entries)
12. ✅ Error handling example
13. ✅ Validation error example
14. ✅ Testnet balance/positions
15. ✅ Code structure (file tree)

### Optional but Impressive Screenshots

16. Grid monitoring in action
17. OCO monitoring
18. Multiple orders in different states
19. Performance metrics
20. Edge case handling

---

## 🎬 Testing Scenarios for Report

### Scenario 1: Day Trader
"Execute multiple quick trades throughout the day"

**Test:**
```bash
# Morning: Buy at market
python src/market_orders.py BTCUSDT BUY 0.01

# Set take-profit
python src/limit_orders.py BTCUSDT SELL 0.01 51000

# Set stop-loss
python src/advanced/stop_limit.py BTCUSDT SELL 0.01 49000 48900
```

### Scenario 2: Large Order Execution
"Need to buy 1 BTC without moving the market"

**Test:**
```bash
python src/advanced/twap.py BTCUSDT BUY 1.0 --duration 30 --intervals 10
```

### Scenario 3: Range Trading
"Market is consolidating between 48k-52k"

**Test:**
```bash
python src/advanced/grid_strategy.py BTCUSDT 48000 52000 10 0.01 --monitor
```

### Scenario 4: Protected Position
"Have a long position and want to protect it"

**Test:**
```bash
python src/advanced/oco.py BTCUSDT SELL 0.01 52000 49000 48900
```

---

## 📊 Performance Metrics to Document

### For Each Order Type, Record:

1. **Execution Time**: How long from command to execution?
2. **Slippage**: Difference between expected and actual price
3. **Success Rate**: How many orders succeeded?
4. **Error Rate**: How many failed and why?

### Example Table for Report:

| Order Type | Tests | Success | Avg Time | Notes |
|------------|-------|---------|----------|-------|
| Market | 10 | 10 | 0.3s | All filled immediately |
| Limit | 8 | 8 | 1.2s | 4 filled, 4 waiting |
| Stop-Limit | 5 | 5 | 0.8s | All placed correctly |
| OCO | 3 | 3 | 1.5s | Both orders placed |
| TWAP | 2 | 2 | 180s | Completed as scheduled |
| Grid | 1 | 1 | 15s | 10 orders placed |

---

## 🐛 Common Issues & Solutions

### Issue 1: "Invalid API Key"
**Solution:** Check .env file, ensure TESTNET=True for testnet keys

### Issue 2: "Insufficient Balance"
**Solution:** Reduce order size or get more testnet funds

### Issue 3: "Symbol Not Found"
**Solution:** Use correct format (BTCUSDT not BTC/USDT)

### Issue 4: "Order Would Immediately Trigger"
**Solution:** Adjust stop/limit prices based on current market

### Issue 5: No Logs Appearing
**Solution:** Check LOG_LEVEL in .env, ensure write permissions

---

## ✅ Final Testing Checklist

Before submission, verify:

- [ ] All order types tested on testnet
- [ ] Screenshots captured for each feature
- [ ] bot.log contains entries for all tests
- [ ] Error handling tested with invalid inputs
- [ ] All validation rules tested
- [ ] Both dry-run and live modes tested
- [ ] Documentation matches actual behavior
- [ ] Code runs without errors
- [ ] README instructions are accurate
- [ ] Report includes all test results

---

## 🎯 Tips for Report

1. **Show Process**: Include both successful and failed attempts
2. **Explain Decisions**: Why did you choose certain parameters?
3. **Document Errors**: Show how bot handles errors gracefully
4. **Compare Modes**: Show difference between dry-run and live
5. **Performance Data**: Include execution times and accuracy
6. **Real Scenarios**: Frame tests as real trading scenarios

---

## 📝 Report Structure Suggestion

### Section 1: Introduction (1 page)
- Bot overview
- Technologies used
- Key features

### Section 2: Architecture (2 pages)
- Code structure
- Module descriptions
- Design decisions

### Section 3: Core Orders (3 pages)
- Market orders
- Limit orders
- Screenshots + explanations

### Section 4: Advanced Orders (5 pages)
- Stop-limit
- OCO
- TWAP
- Grid trading
- Screenshots + explanations for each

### Section 5: Validation & Logging (2 pages)
- Validation examples
- Error handling
- Log samples

### Section 6: Testing Results (2 pages)
- Test scenarios
- Performance metrics
- Edge cases

### Section 7: Conclusion (1 page)
- Summary
- Challenges faced
- Future improvements

**Total: ~16 pages**

---

**Good luck with testing! 🚀**

Remember: The more thorough your testing, the better your report will be!