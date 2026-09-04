# PAIR ANALYSIS - Institutional FX Research Terminal

BiasEngine is a Streamlit FX analysis terminal organized around DATA -> SURPRISE -> REPRICING -> FLOW -> CROSS-ASSET -> TECHNICAL -> ALIGNMENT -> SCORE -> TRADE/WAIT/NO TRADE. It separates structural conditions from marginal repricing and never treats a high rate or yield as an automatic bullish signal.

The application runs without API keys in clearly-labelled DEMO MODE using deterministic seeded observations. Unknown COT, retail, economic, yield, news, and live price fields remain N/A rather than being invented.

## Run

```powershell
py -3.11 -m venv venv
.\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

The terminal includes Overview, 28 Pair Scanner, Currency Matrix, Top Setups, Catalyst Radar, Pair X-Ray, and provider-status views. SQLite persists generated score snapshots in `data/pair_analysis.db`.

## Method

Base scoring uses macro fundamentals (20%), monetary policy (20%), yield/repricing (15%), economic surprise (10%), COT (10%), retail (5%), risk (5%), technicals (10%), and seasonality (5%). Catalyst freshness, contradiction checks, alignment, and price confirmation gate the final action. Provider interfaces live in `data_sources/` and can be replaced independently.

## Security

Keep `.env` local. Never commit API keys or broker credentials. DEMO MODE is not for live trading.

A professional-grade Python scanner that detects a specific 4-hour candle time-alignment setup across all 28 major and minor currency pairs. Monitor the market 24/5 with real-time alerts, historical backtesting, and a Streamlit dashboard.

## 🎯 Core Strategy

**The Setup:**
1. Monitor the **8:00 – 12:00** 4-hour candle (Nairobi time)
2. Detect if the **Low** of this candle was formed at **11:50-11:59** (very late in the candle)
3. Once the 12:00 4H candle opens, check if price **takes out** (breaks below) that 11:59 low within the first 1-5 minutes
4. If both conditions are met → **BUY signal** targeting the **midpoint (50%)** of the entire 8am 4H candle

**Why this works:**
- Late candle lows show trapped buyers (institutional moves)
- Breakout confirmation in the next candle validates the setup
- 50% midpoint provides a balanced risk/reward target

## ✨ Features

- ✅ **Real-time scanning** across 28 major + minor currency pairs
- ✅ **Multi-channel alerts**: Console, Telegram, Discord, Email, Sound
- ✅ **Timezone handling**: Easy configuration for any broker timezone (Nairobi/UTC)
- ✅ **Streamlit Dashboard**: Beautiful real-time visualization
- ✅ **Historical backtesting**: Test past 3-6 months of data
- ✅ **MetaTrader5 integration**: Direct connection to MT5 terminal
- ✅ **Detailed logging**: Track every scan and signal
- ✅ **Easy pair management**: Add/remove pairs in one place
- ✅ **Signal filtering**: Only trade very late lows (>11:50)
- ✅ **Modular code**: Clean separation of concerns, well-commented

## 🏗️ Architecture

```
biasflo-forex-scanner/
├── src/forex_scanner/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── mt5_connector.py         # MT5 connection & data retrieval
│   ├── scanner.py               # Core scanning logic
│   ├── alerts.py                # Multi-channel alerting
│   ├── data_processor.py        # Backtesting & data processing
│   └── utils.py                 # Helper functions
├── dashboard/
│   └── app.py                   # Streamlit dashboard
├── backtest/
│   └── backtest.py              # Standalone backtest script
├── main.py                      # Live scanner entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.8+** installed
- **MetaTrader 5** desktop terminal installed and logged into your broker account
- **Git** (optional, for version control)

### 2. Installation

```bash
# Clone or download the project
cd c:\Users\Creative Kigen\Desktop\BiasFlo\vs

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy example config
copy .env.example .env

# Edit .env with your settings
# - Add your MT5 account details
# - Configure alert channels (Telegram, Discord, etc.)
# - Set timezone if not Nairobi
```

**Sample .env:**
```
MT5_ACCOUNT=1234567
MT5_PASSWORD=your_password
MT5_SERVER=JustMarkets-Server
MARKET_TIMEZONE=Africa/Nairobi

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

SOUND_ENABLED=true
```

### 4. Run the Scanner

**Option A: Live Monitor (Recommended)**
```bash
python main.py
```
- Continuously scans every 5 minutes
- Monitors all 28 pairs
- Checks for breakouts during 12:00 hour
- Sends real-time alerts to configured channels

**Option B: Streamlit Dashboard**
```bash
streamlit run dashboard/app.py
```
- Open browser to `http://localhost:8501`
- Connect to MT5 and monitor in real-time
- Run backtests directly from the UI

**Option C: Backtest Historical Data**
```bash
# Backtest all pairs (last 90 days)
python backtest/backtest.py

# Backtest single pair for custom date range
python backtest/backtest.py --pair EURUSD --start 2024-01-01 --end 2024-03-31

# Show verbose output
python backtest/backtest.py --verbose
```

## 📊 Monitoring & Alerts

### Alert Types

The scanner can send alerts through multiple channels:

| Channel | Configuration | Notes |
|---------|---------------|-------|
| **Console** | Always on | Real-time logs in terminal |
| **Telegram** | Bot token + Chat ID | Get instant phone notifications |
| **Discord** | Webhook URL | Direct server alerts |
| **Email** | SMTP credentials | Daily summary emails |
| **Sound** | WAV file | Desktop alert sound |

### Example Alert

```
================================================================================
🚨 FOREX SCANNER ALERT - 11:52:30
================================================================================
✓ EURUSD: Late 8am 4H Candle Low Detected
Ready to monitor for 12:00 breakout

Details:
  • Pair: EURUSD
  • Low Price: 1.09456
  • Low Time (Nairobi): 11:51:32
  • Low Position: Minute 231 of 4H candle
  • Candle High: 1.10234
  • Target (50% midpoint): 1.09845
  • Detected At: 2024-09-02 11:52:30
================================================================================
```

## 🧪 Backtesting

### Running Backtests

```bash
# Backtest all pairs for last 3 months
python backtest/backtest.py --start 2024-06-01 --end 2024-09-01

# Backtest single pair
python backtest/backtest.py --pair GBPUSD --start 2024-01-01 --end 2024-12-31
```

### Backtest Results

The scanner generates two CSV files:

1. **backtest_results.csv** - Summary statistics:
   - Total setups found
   - Total breakouts detected
   - Win rate percentage
   - Setup-to-breakout conversion rate

2. **signal_details.csv** - Detailed trades:
   - Date, low price, breakout price
   - Target price and pips
   - Profitable/losing trades

### Example Output

```
BACKTEST RESULTS SUMMARY

Pair         | Setups | Breakouts | Profitable | Losing | Win Rate | Setup→Breakout
EURUSD       |   24   |    15     |     10     |   5    |  66.7%   |    62.5%
GBPUSD       |   19   |    11     |      7     |   4    |  63.6%   |    57.9%
USDJPY       |   22   |    14     |      9     |   5    |  64.3%   |    63.6%
```

## ⚙️ Configuration Guide

### config.py - Main Settings

```python
# Scanner Parameters
CANDLE_START_HOUR = 8           # 8:00 AM start
CANDLE_END_HOUR = 12            # 12:00 PM end
LATE_LOW_THRESHOLD_MINUTES = 50 # Low must form after 11:50
BREAKOUT_WATCH_WINDOW_MINUTES = 5  # Check first 5 min after 12:00

# Timezone (change as needed)
MARKET_TIMEZONE = "Africa/Nairobi"
UTC_OFFSET_HOURS = 3

# Forex Pairs (easily add/remove)
FOREX_PAIRS = [
    # Majors (7)
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    # Major Crosses (12)
    "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD",
    "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD",
    "CHFJPY", "CADCHF", "AUDCHF", "NZDCHF",
    # Minor Pairs (9)
    "JPYAUD", "JPYNZD", "AUDJPY", "NZDJPY", "AUDUSD",
    "AUDNZD", "NZDUSD", "CADJPY", "USDSEK"
]
```

### MT5 Connection

Ensure MetaTrader5 is installed and running before starting the scanner:

1. Launch MT5 terminal
2. Login to your broker account
3. Keep MT5 running while scanner is active
4. Scanner will auto-connect on startup

## 📈 Understanding the Setup

### Late Low Detection (11:50-11:59)

The scanner identifies when price makes a new 4-hour low in the final minutes:

```
11:50-11:59 = "Late Low Zone"
If Low is formed here → Setup Triggered ✓
```

**Why late low matters:**
- Shows institutional buying/support failure
- Indicates trapped buyers (potential reversal)
- Creates strong pressure for next candle breakout

### Breakout Confirmation (12:00-12:05)

Once the 12:00 candle opens, the scanner watches for the low to be taken out:

```
12:00 Candle Opens
12:00-12:05 = "Breakout Watch Window"
If price goes below 11:59 low → BREAKOUT ✓ → Ready to Trade!
```

**Signal strength is based on:**
- **WEAK**: Barely below low (<5 pips)
- **MODERATE**: Moderate breakdown (5-15 pips)
- **STRONG**: Deep breakdown (>15 pips)

## 🔧 Advanced Usage

### Adding Custom Pairs

Edit `config.py`:

```python
FOREX_PAIRS = [
    # Your existing pairs...
    "EURUSD", "GBPUSD",
    # Add new ones:
    "XAUUSD",  # Gold
    "SPX500",  # SP500
]
```

### Changing Timezone

For different broker timezones:

```python
# London (GMT)
MARKET_TIMEZONE = "Europe/London"
UTC_OFFSET_HOURS = 0

# New York (EST/EDT)
MARKET_TIMEZONE = "America/New_York"
UTC_OFFSET_HOURS = -5

# Tokyo (JST)
MARKET_TIMEZONE = "Asia/Tokyo"
UTC_OFFSET_HOURS = 9
```

### Custom Alert Channels

Extend `alerts.py` to add new alert types:

```python
class SlackAlert(AlertChannel):
    def send(self, message: str, data: dict) -> bool:
        # Implement Slack webhook
        pass
    
    def is_available(self) -> bool:
        return config.SLACK_ENABLED
```

### Adjusting Breakout Window

Change how many minutes to watch after 12:00:

```python
BREAKOUT_WATCH_WINDOW_MINUTES = 10  # Watch first 10 minutes instead of 5
```

## 📝 Logging

All activity is logged to:

- **Console**: Real-time output during execution
- **logs/scanner.log**: Live scanner logs
- **logs/dashboard.log**: Dashboard-specific logs
- **logs/backtest.log**: Backtest execution logs

Logs rotate automatically to prevent huge files (10MB per file, keeps 5 backups).

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

Configure in `.env`:
```
LOG_LEVEL=INFO       # Set to DEBUG for verbose output
DEBUG_MODE=false     # Set to true for extra debugging
```

## 🐛 Troubleshooting

### MT5 Connection Issues

```
Error: MT5 initialization failed
→ Ensure MetaTrader5 desktop terminal is running and logged in
→ Check account number and password in .env
→ Verify server name matches your broker
```

### No Setups Detected

```
→ Check if current time is between 8:00-12:00 Nairobi time
→ Verify timezone in config matches your broker
→ Check data availability for the pair in MT5
```

### Alerts Not Sending

```
Telegram: Verify bot token and chat ID are correct
Discord: Test webhook URL in browser
Email: Check SMTP credentials and "Allow Less Secure Apps" setting
```

### Import Errors

```
→ Ensure all packages installed: pip install -r requirements.txt
→ Check Python version: python --version (need 3.8+)
→ Activate virtual environment: venv\Scripts\activate
```

## 📚 File Reference

| File | Purpose |
|------|---------|
| `config.py` | Central configuration, pairs, timezone |
| `mt5_connector.py` | MT5 connection and data retrieval |
| `scanner.py` | Core setup/breakout detection logic |
| `alerts.py` | Multi-channel alert sending |
| `data_processor.py` | Backtesting and historical analysis |
| `utils.py` | Helper functions and utilities |
| `main.py` | Live scanner entry point |
| `app.py` | Streamlit dashboard |
| `backtest.py` | Standalone backtest script |

## 🤝 Contributing

To add improvements:

1. Create a new branch: `git checkout -b feature/new-feature`
2. Make changes and test thoroughly
3. Update documentation as needed
4. Submit pull request with description

## 📄 License

This project is proprietary. Use only for your own trading purposes.

## ⚠️ Disclaimer

**This scanner is for educational and research purposes only.** Trading foreign exchange carries substantial risk and may not be suitable for all investors. Past performance is not indicative of future results. The developer assumes no responsibility for trading losses or decisions made based on this tool.

Always:
- Test strategies thoroughly before trading real money
- Use appropriate position sizing and risk management
- Keep stops in place to limit losses
- Never risk more than you can afford to lose

## 🆘 Support

For issues, questions, or feature requests:

- Check the logs in `logs/` folder
- Review this README for common issues
- Enable `DEBUG_MODE=true` for verbose logging
- Check MT5 terminal for data/connection issues

## 🎓 Learning Resources

- MetaTrader5 Documentation: https://www.metatrader5.com/en/terminal/help
- Python: https://docs.python.org/3/
- Streamlit: https://docs.streamlit.io/
- Pandas: https://pandas.pydata.org/docs/

---

**Happy Trading! 📈**

*Forex Scanner v1.0.0 | Built with Python, MetaTrader5, and Streamlit*
