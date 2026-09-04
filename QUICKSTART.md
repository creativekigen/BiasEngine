# 🚀 Quick Start Guide

Get your Forex Scanner running in 5 minutes!

## Step 1: Install Python Dependencies (2 min)

```bash
# Navigate to project folder
cd c:\Users\Creative Kigen\Desktop\BiasFlo\vs

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install all packages
pip install -r requirements.txt
```

✓ Done! All libraries installed.

---

## Step 2: Set Up Configuration (1 min)

```bash
# Copy the example config
copy .env.example .env

# Open .env in your editor and fill in:
# 1. Your MT5 account number
# 2. Your MT5 password
# 3. Your broker server name (e.g., JustMarkets-Server)
```

**Minimum configuration:**
```
MT5_ACCOUNT=123456789
MT5_PASSWORD=your_password
MT5_SERVER=JustMarkets-Server
```

✓ Config ready!

---

## Step 3: Start MetaTrader 5

1. Launch **MetaTrader 5** on your computer
2. **Log in** to your broker account
3. **Keep MT5 running** - scanner will connect to it

✓ MT5 ready!

---

## Step 4: Choose Your Mode (2 min)

### 🔴 LIVE SCANNING (Recommended)

```bash
python main.py
```

**What happens:**
- Connects to your MT5 terminal
- Scans all 28 pairs every 5 minutes
- Watches for 8:00 AM 4H candle lows
- Monitors 12:00 PM breakouts
- Sends real-time alerts when setup triggers

**Example output:**
```
================================================================================
SCAN - 2024-09-02 11:51:30 | Candle: 94% complete
================================================================================
✓ Found 3 late 8am 4H lows:
  • EURUSD: Low=1.09456 at 11:51
  • GBPUSD: Low=1.27123 at 11:52
  • USDJPY: Low=144.567 at 11:50
```

---

### 📊 STREAMLIT DASHBOARD (Visual)

```bash
streamlit run dashboard/app.py
```

**What opens:**
- Beautiful web dashboard at `http://localhost:8501`
- Live pair monitoring
- Manual scan button
- Backtest tools
- Alert status

**Perfect for:**
- Watching the scanner while working
- Running ad-hoc backtests
- Monitoring alert channels

---

### 📈 BACKTEST HISTORICAL DATA

```bash
# Test last 90 days
python backtest/backtest.py

# Test specific date range
python backtest/backtest.py --start 2024-06-01 --end 2024-09-01

# Test single pair
python backtest/backtest.py --pair EURUSD --start 2024-01-01 --end 2024-12-31
```

**Output:**
```
BACKTEST RESULTS SUMMARY

Pair         | Setups | Breakouts | Win Rate | Setup→Breakout
EURUSD       |   24   |    15     |  66.7%   |    62.5%
GBPUSD       |   19   |    11     |  63.6%   |    57.9%
USDJPY       |   22   |    14     |  64.3%   |    63.6%
```

---

## ✅ Checklist

Before you start, ensure:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] MetaTrader 5 installed and running
- [ ] Logged into your broker account in MT5
- [ ] .env file created with your MT5 credentials
- [ ] Virtual environment activated
- [ ] All requirements installed (`pip list | grep MetaTrader5`)

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "MT5 initialization failed" | Launch MT5 first, then start scanner |
| "No candles retrieved" | Check pair is enabled in MT5 market watch |
| "ImportError: MetaTrader5" | Run `pip install MetaTrader5==5.0.45` |
| "Alerts not sending" | Check .env has correct bot tokens |

## 📖 Next Steps

1. **Understand the setup** → Read main README.md
2. **Configure alerts** → Follow "Alert Types" in README
3. **Add custom pairs** → Edit config.py FOREX_PAIRS list
4. **Monitor live** → Run `python main.py`
5. **Backtest** → Run `python backtest/backtest.py`

---

## 🎯 What to Expect

**When running the live scanner:**

- **8:00-12:00 window:** Scanner looks for late 4H candle lows
- **11:50-11:59:** If low forms here, setup is triggered
- **12:00 candle opens:** Scanner watches for breakout (5 minutes)
- **Breakout occurs:** Real-time alert sent to all channels
- **Next cycle:** Process repeats at next 8:00 AM

**Typical daily activity (Nairobi timezone):**
```
08:00 - Candle begins
11:50 - Late low detection window opens
11:59 - Last chance for setup
12:00 - Next candle opens, breakout confirmation window
12:05 - Breakout window closes
13:00 - No more setups until next day's 8:00 AM
```

---

## 🔔 Alert Example

When a setup is detected and confirmed with breakout:

**Console:**
```
✓ EURUSD: 12:00 4H Candle BREAKOUT - STRONG
Price took out the 8am low! READY TO TRADE!
```

**Telegram/Discord:** (if enabled)
```
🚀 EURUSD: 12:00 4H BREAKOUT - STRONG
Original Low: 1.09456
Breakout Price: 1.09445
Target: 1.09845
Distance to Target: 400 pips
```

---

## 💡 Pro Tips

1. **Run 24/5:** Keep the scanner running during forex market hours
2. **Monitor logs:** Check `logs/scanner.log` for detailed activity
3. **Test first:** Always backtest new pairs before trading
4. **Adjust timezone:** If your broker uses different timezone, change in config.py
5. **Set daily restart:** Use Windows Task Scheduler to restart scanner daily

---

## 📞 Need Help?

1. Check README.md for detailed documentation
2. Review logs in `logs/` folder
3. Enable `DEBUG_MODE=true` in .env for verbose output
4. Verify MT5 is connected: Try manual symbol lookup

---

**You're ready! Start scanning! 🚀📈**
