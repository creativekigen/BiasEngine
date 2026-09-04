# Architecture & Design Guide

## System Overview

The Forex Scanner is built with a modular, layered architecture that separates concerns and enables easy testing, maintenance, and extension.

```
┌─────────────────────────────────────────────────────────────┐
│                  USER INTERFACES                            │
├─────────────────┬─────────────────┬───────────────────────────┤
│ Live Scanner    │ Streamlit       │ Backtest Script           │
│ (main.py)       │ (dashboard)     │ (backtest.py)             │
└─────────┬───────┴────────┬────────┴───────────┬──────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼──────────────┐
│                 BUSINESS LOGIC LAYER                         │
├──────────────────────────────────────────────────────────────┤
│ Scanner        │ Alert Manager  │ Data Processor             │
│ (scanner.py)   │ (alerts.py)    │ (data_processor.py)        │
└─────────┬────────────────┬──────────────────┬────────────────┘
          │                │                  │
┌─────────▼────────────────▼──────────────────▼────────────────┐
│               DATA & INTEGRATION LAYER                       │
├──────────────────────────────────────────────────────────────┤
│ MT5 Connector            │ Utilities & Helpers               │
│ (mt5_connector.py)       │ (utils.py)                        │
└──────────────┬────────────────────────┬──────────────────────┘
               │                        │
┌──────────────▼────────────────────────▼──────────────────────┐
│             EXTERNAL SERVICES & DATA                         │
├──────────────────────────────────────────────────────────────┤
│ MetaTrader5 Terminal   │ Telegram   │ Discord   │ Email      │
│ (Market Data)          │ Bot        │ Webhook   │ SMTP       │
└──────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. **config.py** - Configuration Management
**Responsibility:** Centralized configuration for the entire system

**Key Classes:**
- `Config`: Pydantic BaseSettings model for all configuration
- `AlertType`: Enum for alert channel types

**Key Variables:**
- `MARKET_TIMEZONE`: Market timezone (default: Africa/Nairobi)
- `CANDLE_START_HOUR`, `CANDLE_END_HOUR`: 4H candle window
- `LATE_LOW_THRESHOLD_MINUTES`: Threshold for late low detection
- `BREAKOUT_WATCH_WINDOW_MINUTES`: Window to watch after 12:00
- `FOREX_PAIRS`: List of all 28 currency pairs to monitor
- Alert settings (Telegram, Discord, Email, Sound)

**Design Pattern:** Singleton (loaded once at startup)

---

### 2. **mt5_connector.py** - MT5 Integration Layer
**Responsibility:** Manage all MetaTrader5 connections and data retrieval

**Key Class:**
- `MT5Connector`: Wrapper around MetaTrader5 API

**Key Methods:**
- `connect()`: Initialize MT5 connection
- `get_candles()`: Retrieve OHLC data for a pair
- `get_latest_minute_candles()`: Get 1-minute candles
- `get_bid_ask()`: Get current market prices
- `convert_to_nairobi_time()`: UTC ↔ Nairobi timezone conversion

**Design Pattern:** Wrapper/Adapter pattern over MT5 API
**Isolation:** All MT5 calls go through this module (no direct MT5 imports elsewhere)

---

### 3. **scanner.py** - Core Scanning Logic
**Responsibility:** Detect 8am low and 12pm breakouts

**Key Classes:**
- `LowSignal`: Dataclass representing a detected 8am late low
- `BreakoutSignal`: Dataclass representing a detected breakout
- `ForexScanner`: Main scanning engine

**Key Methods:**
- `scan_4h_candle()`: Detect late low in 8am 4H candle
- `check_12pm_breakout()`: Verify breakout in 12pm candle
- `scan_all_pairs()`: Scan all 28 pairs
- `check_all_breakouts()`: Check all active signals for breakout

**Algorithm:**

```
scan_4h_candle(pair):
  1. Get 1-minute candles for 8:00-12:00 window
  2. Find the absolute low in this window
  3. Check if low was formed between 11:50-11:59
  4. If yes: Calculate 50% midpoint target, return LowSignal
  
check_12pm_breakout(pair, low_signal):
  1. Get 1-minute candles for first 5 minutes of 12:00 hour
  2. Find minimum low in this window
  3. If min_low < low_signal.low_price: Return BreakoutSignal
```

---

### 4. **alerts.py** - Multi-Channel Alerting
**Responsibility:** Send alerts through configurable channels

**Key Classes:**
- `AlertChannel`: Abstract base class for all alert types
- `ConsoleAlert`: Print to stdout
- `TelegramAlert`: Send via Telegram bot
- `DiscordAlert`: Send via Discord webhook
- `EmailAlert`: Send via SMTP
- `SoundAlert`: Play system sound
- `AlertManager`: Orchestrates all channels

**Design Pattern:** Strategy pattern + Factory pattern
**Extension Point:** Easy to add new alert types by extending `AlertChannel`

**Alert Flow:**
```
Signal Detected
    ↓
AlertManager.send_breakout_alert(signal)
    ↓
For each enabled channel:
  - ConsoleAlert.send() → Print to console
  - TelegramAlert.send() → HTTP to Telegram
  - DiscordAlert.send() → HTTP to Discord Webhook
  - EmailAlert.send() → SMTP
  - SoundAlert.send() → Play sound
```

---

### 5. **data_processor.py** - Backtesting & Analysis
**Responsibility:** Process historical data and run backtests

**Key Class:**
- `DataProcessor`: Historical data analysis engine

**Key Methods:**
- `load_historical_data()`: Fetch candles from MT5 for date range
- `resample_to_4h_nairobi()`: Resample 1-min to 4H candles
- `backtest_setup()`: Test setup on historical data for one pair
- `backtest_all_pairs()`: Run full backtest across all pairs
- `save_backtest_results()`: Export results to CSV

**Backtest Output:**
- Total setups found
- Total breakouts detected
- Win rate percentage
- Setup-to-breakout conversion rate
- Detailed trade-by-trade results

---

### 6. **utils.py** - Utility Functions
**Responsibility:** Common helper functions

**Key Functions:**
- `setup_logging()`: Configure logging for the app
- `get_nairobi_time()`: Get current Nairobi time
- `get_4h_candle_info()`: Get progress on current 4H candle
- `format_price()`, `format_pips()`: Number formatting
- `time_to_nairobi()`, `time_to_utc()`: Timezone conversion
- `is_market_open()`: Check if forex market is trading

**Key Classes:**
- `ScannerStats`: Track cumulative statistics

---

## Data Flow

### Live Scanning Flow

```
main.py
  └─ LiveScanner.run()
      ├─ Every 5 minutes: scan_setup()
      │   ├─ For each pair:
      │   │   ├─ scanner.scan_4h_candle(pair)
      │   │   │   ├─ mt5_connector.get_candles()
      │   │   │   ├─ Detect late low
      │   │   │   └─ Return LowSignal if found
      │   │   └─ Store in scanner.active_breakout_watches
      │   └─ alert_manager.send_low_signal_alert()
      │
      ├─ Every 1 minute: check_breakouts()
      │   ├─ For each active low:
      │   │   ├─ scanner.check_12pm_breakout()
      │   │   │   ├─ mt5_connector.get_latest_minute_candles()
      │   │   │   ├─ Check if low was taken out
      │   │   │   └─ Return BreakoutSignal if found
      │   │   └─ alert_manager.send_breakout_alert()
      │
      └─ Every 30 minutes: print_status()
```

### Backtest Flow

```
backtest.py --pair EURUSD --start 2024-01-01 --end 2024-12-31
  └─ DataProcessor.backtest_setup()
      ├─ load_historical_data() → Get all 1-min candles
      ├─ For each day:
      │   ├─ Get 8am 4H candle OHLC
      │   ├─ Check for late low
      │   ├─ Get next day's 12pm 1-min candles
      │   ├─ Check for breakout
      │   └─ Record result (profitable/losing)
      ├─ Calculate statistics (win rate, setup-to-breakout %)
      └─ Return results dictionary
```

### Dashboard Flow

```
Streamlit (app.py)
  ├─ Load config
  ├─ Display UI
  ├─ User clicks "Connect to MT5"
  │   └─ mt5_connector.connect()
  ├─ User clicks "Run Scanner"
  │   ├─ scanner.scan_all_pairs()
  │   ├─ Display found setups
  │   └─ scanner.check_all_breakouts()
  └─ Display results
```

## Design Patterns Used

### 1. **Singleton Pattern**
- `config` object - loaded once, used everywhere
- `_alert_manager` - single instance for alerts
- `_stats` - global statistics tracker

### 2. **Strategy Pattern**
- `AlertChannel` abstract class with multiple implementations
- Easy to add new alert types without changing AlertManager

### 3. **Factory Pattern**
- `AlertManager.channels` dictionary mapping types to instances
- `get_alert_manager()` factory function

### 4. **Wrapper/Adapter Pattern**
- `MT5Connector` wraps MetaTrader5 API
- Abstracts away MT5 implementation details

### 5. **Dataclass Pattern**
- `LowSignal`, `BreakoutSignal` - immutable signal containers
- Clean data representation

## Key Design Decisions

### 1. **Why Separate Concerns?**
- **MT5 Layer**: If changing brokers, only MT5Connector changes
- **Scanner Layer**: Pure logic, testable without MT5
- **Alert Layer**: Easy to add new channels without touching scanner

### 2. **Why Timezone Handling in MT5Connector?**
- All time conversions happen at the boundary between app and MT5
- Rest of app works purely in Nairobi time

### 3. **Why Active Breakout Watches Dictionary?**
- Avoids re-scanning entire dataset for each pair
- Only checks pairs with actual setups
- Cleans up after trade (memory efficient)

### 4. **Why Signal Dataclasses?**
- Clear data contracts
- Immutable (prevents accidental changes)
- Easy to serialize for logging/alerts

## Extension Points

### Add New Alert Channel
```python
class SlackAlert(AlertChannel):
    def send(self, message: str, data: dict) -> bool:
        # Implement Slack webhook
        pass
    
    def is_available(self) -> bool:
        return config.SLACK_ENABLED

# Register in config.py
ALERT_TYPES = [AlertType.CONSOLE, AlertType.SLACK, ...]
```

### Add New Pair
```python
# In config.py, just add to FOREX_PAIRS list
FOREX_PAIRS = [
    # ... existing pairs
    "XAUUSD",  # Gold
    "BTCUSD",  # Bitcoin
]
```

### Change Candle Window
```python
# In config.py
CANDLE_START_HOUR = 9      # 9:00 AM instead of 8:00
CANDLE_END_HOUR = 13       # 1:00 PM instead of 12:00
```

### Add Custom Data Analysis
```python
# In data_processor.py
def analyze_correlation(self, pair1: str, pair2: str):
    # Load data for both pairs
    # Calculate correlation
    # Return results
```

## Performance Considerations

### Memory
- `active_breakout_watches`: Dict with max 28 entries (one per pair)
- Signals are cleaned up after breakout confirmation
- No data cached beyond current scan

### CPU
- Scans run every 5 minutes (not continuous)
- 1-minute candle retrieval only during 12:00 hour
- Parallel pair scanning possible (currently sequential)

### Network
- Only fetches data when needed (not polling 24/7)
- MT5 connection reused (not new connection per pair)
- Alert sends are async-capable (could be threaded)

## Testing Strategy

### Unit Tests (to add)
- `test_scanner.py`: Test signal detection logic
- `test_alerts.py`: Test alert formatting
- `test_utils.py`: Test timezone conversions

### Integration Tests (to add)
- Mock MT5 with test data
- Verify complete pipeline works
- Test all alert channels

### Manual Testing
- `test.py` script for quick diagnostics
- Backtest for historical validation
- Live monitoring in sandbox account

## Error Handling

### Connection Errors
- MT5 connection fails → Log and retry
- Alert send fails → Log and continue (don't break scanning)

### Data Errors
- No candles available → Log warning and skip
- Timezone conversion error → Fall back to UTC

### Configuration Errors
- Missing .env → Use defaults with warnings
- Invalid pair → Skip and log warning

## Logging Strategy

**Log Levels:**
- `DEBUG`: Detailed execution flow, every scan result
- `INFO`: Key events (connections, setups found, alerts sent)
- `WARNING`: Recoverable issues (no data, config missing)
- `ERROR`: Fatal issues requiring attention

**Log Files:**
- `logs/scanner.log`: Live scanner activity
- `logs/dashboard.log`: Dashboard interactions
- `logs/backtest.log`: Backtest execution

## Future Enhancements

1. **Real-time Dashboard**: WebSocket updates instead of page refresh
2. **Mobile Alerts**: Push notifications to mobile apps
3. **Multi-broker Support**: Abstract MT5 into broker interface
4. **Machine Learning**: Predict breakout probability based on patterns
5. **Risk Management**: Auto-position sizing based on account equity
6. **Performance Analytics**: Track statistical performance over time
7. **Optimization**: Parallel pair scanning for faster processing
8. **Validation**: Unit/integration tests for all modules

---

**This architecture ensures the Forex Scanner is maintainable, extensible, and production-ready.**
