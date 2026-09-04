# 📖 Forex Scanner - Complete Documentation Index

Welcome! This document guides you to the right resource for what you need.

## 🚀 Getting Started

**New to the scanner?** Start here:

1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
   - Installation steps
   - Running the scanner
   - Quick troubleshooting

2. **[README.md](README.md)** - Comprehensive documentation
   - Feature overview
   - Configuration guide
   - Backtesting instructions
   - Complete reference

## 📂 File Guide

### Core Application Files

| File | Purpose | Read When |
|------|---------|-----------|
| `main.py` | Live scanner entry point | Running live monitoring |
| `dashboard/app.py` | Streamlit web dashboard | Want visual interface |
| `backtest/backtest.py` | Historical backtesting | Testing strategy |
| `setup.py` | Initial setup wizard | First time setup |
| `test.py` | Diagnostic test suite | Troubleshooting issues |

### Source Code Modules

| File | Purpose | Read When |
|------|---------|-----------|
| `src/forex_scanner/config.py` | Configuration management | Changing settings |
| `src/forex_scanner/mt5_connector.py` | MT5 integration | Understanding data flow |
| `src/forex_scanner/scanner.py` | Core scanning logic | Deep dive into how detection works |
| `src/forex_scanner/alerts.py` | Alert system | Setting up notifications |
| `src/forex_scanner/data_processor.py` | Data analysis | Understanding backtesting |
| `src/forex_scanner/utils.py` | Helper functions | Reference utilities |

### Configuration Files

| File | Purpose | Read When |
|------|---------|-----------|
| `.env.example` | Configuration template | Setting up your account |
| `.env` | Your actual configuration | Daily use (keep secret!) |
| `.gitignore` | Version control settings | Using Git |
| `requirements.txt` | Python dependencies | Installing packages |

### Documentation Files

| File | Purpose | Read When |
|------|---------|-----------|
| `README.md` | Main documentation | Learning the full system |
| `QUICKSTART.md` | Fast setup guide | Getting started quickly |
| `ARCHITECTURE.md` | System design | Understanding code structure |
| `CHANGELOG.md` | Version history | Checking what's new |
| `INDEX.md` | This file! | Navigating the project |

---

## 🎯 Find What You Need

### "I want to..."

#### **Run the scanner**
→ [QUICKSTART.md - Step 4](QUICKSTART.md#step-4-choose-your-mode-2-min)
```bash
python main.py
```

#### **Use the dashboard**
→ [QUICKSTART.md - Step 4](QUICKSTART.md#-streamlit-dashboard-visual)
```bash
streamlit run dashboard/app.py
```

#### **Test past data**
→ [QUICKSTART.md - Step 4](QUICKSTART.md#-backtest-historical-data)
```bash
python backtest/backtest.py
```

#### **Set up Telegram alerts**
→ [README.md - Alert Types](README.md#alert-types)
1. Create Telegram bot
2. Get bot token and chat ID
3. Add to .env file

#### **Add a new currency pair**
→ [README.md - Adding Custom Pairs](README.md#adding-custom-pairs)
Edit `src/forex_scanner/config.py`:
```python
FOREX_PAIRS.append("XAUUSD")
```

#### **Change timezone**
→ [README.md - Changing Timezone](README.md#changing-timezone)
Edit `src/forex_scanner/config.py`:
```python
MARKET_TIMEZONE = "Europe/London"
```

#### **Understand how it works**
→ [ARCHITECTURE.md](ARCHITECTURE.md)
- System overview diagram
- Module breakdown
- Data flow explanation

#### **Fix a problem**
→ [README.md - Troubleshooting](README.md#-troubleshooting)
or
→ Run diagnostics:
```bash
python test.py
```

#### **Change the 4H window**
→ [README.md - Advanced Usage](README.md#adjusting-breakout-window)
Edit `src/forex_scanner/config.py`:
```python
CANDLE_START_HOUR = 9
CANDLE_END_HOUR = 13
```

#### **Add Discord alerts**
→ [README.md - Alert Types](README.md#alert-types)
Get webhook URL and add to .env:
```
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

#### **Understand the strategy**
→ [README.md - Understanding the Setup](README.md#-understanding-the-setup)
Shows exactly how setups are detected and traded.

#### **See code examples**
→ [README.md - Advanced Usage](README.md#-advanced-usage)
Custom implementations and extensions.

---

## 📊 Module Purpose Map

```
User Interaction
    ↓
┌───────────────────────────────────────┐
│ main.py (Live)                        │
│ dashboard/app.py (Web)                │
│ backtest/backtest.py (Historical)     │
└───────┬───────────────────────────────┘
        ↓
┌───────────────────────────────────────┐
│ config.py (Settings)                  │
│ mt5_connector.py (Market Data)        │
│ scanner.py (Detection Logic)          │
│ alerts.py (Notifications)             │
│ data_processor.py (Analysis)          │
│ utils.py (Helpers)                    │
└───────┬───────────────────────────────┘
        ↓
External Systems
(MT5, Telegram, Discord, Email)
```

---

## ✅ Quick Checklist

### First Time Setup

- [ ] Read QUICKSTART.md
- [ ] Run `python setup.py`
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in MT5 credentials
- [ ] Launch MetaTrader 5
- [ ] Run `python test.py` to verify
- [ ] Run `python main.py` to start

### Before Going Live

- [ ] Backtest for past 3 months: `python backtest/backtest.py`
- [ ] Verify alert channels work (test Telegram, Discord, etc.)
- [ ] Check logs are being created
- [ ] Verify timezone matches your broker
- [ ] Test with 1-2 pairs first

### During Live Trading

- [ ] Monitor logs regularly
- [ ] Verify scanner is running: `python main.py`
- [ ] Check dashboard: `streamlit run dashboard/app.py`
- [ ] Record all alerts sent
- [ ] Follow your trading plan (don't deviate on signals)

---

## 📚 Documentation Structure

### README.md (Comprehensive Reference)
- Feature overview
- Installation & setup
- How to use each mode
- Configuration options
- Troubleshooting guide
- Advanced customization

### QUICKSTART.md (Fast Setup)
- 5-minute initialization
- Step-by-step instructions
- Common issues
- Next steps

### ARCHITECTURE.md (Technical Deep Dive)
- System design
- Module breakdown
- Data flow diagrams
- Design patterns
- Extension points
- Performance notes

### This File (INDEX.md - Navigation)
- Quick links
- File purpose guide
- "How do I..." answers
- Checklist

---

## 🔍 Search Guide

**Looking for information about:**

| Topic | Location |
|-------|----------|
| Installation | QUICKSTART.md, README.md |
| MT5 setup | QUICKSTART.md, Troubleshooting |
| Running the scanner | QUICKSTART.md, README.md |
| Dashboard usage | README.md, main.py docstring |
| Backtesting | QUICKSTART.md, backtest.py |
| Pair management | config.py, README.md |
| Alerts | alerts.py, README.md |
| Timezone | config.py, ARCHITECTURE.md |
| Logging | utils.py, README.md |
| Code structure | ARCHITECTURE.md |
| Error fixing | test.py, README.md |
| Performance | ARCHITECTURE.md |

---

## 💡 Recommended Learning Path

### Path 1: "I Just Want to Run It" (30 minutes)
1. QUICKSTART.md (5 min)
2. Run setup.py (2 min)
3. Configure .env (5 min)
4. Run main.py (1 min)
5. Test alerts (5 min)
6. Run backtest (10 min)

### Path 2: "I Want to Understand It" (2 hours)
1. README.md - Core Logic section (15 min)
2. ARCHITECTURE.md - System Overview (20 min)
3. Review config.py (10 min)
4. Review scanner.py (20 min)
5. Review alerts.py (15 min)
6. Run test.py and review output (10 min)
7. Run main.py with DEBUG_MODE=true (20 min)
8. Backtest and analyze results (10 min)

### Path 3: "I Want to Customize It" (4 hours)
1. Complete Path 2 (2 hours)
2. ARCHITECTURE.md - Extension Points (20 min)
3. Review mt5_connector.py (20 min)
4. Review data_processor.py (20 min)
5. Implement custom changes (1 hour)
6. Test changes (20 min)

---

## 🆘 Troubleshooting Navigation

| Problem | Solution |
|---------|----------|
| Installation fails | README.md → Troubleshooting |
| MT5 won't connect | test.py → Run TEST 2 |
| No pairs found | test.py → Run TEST 4 |
| Alerts not working | test.py → Run TEST 3 |
| Wrong timezone | config.py line 7, then test.py |
| Code errors | test.py → Run all tests |
| Performance issues | ARCHITECTURE.md → Performance |

---

## 📞 Getting Help

1. **Check documentation first:**
   - Does README.md answer it?
   - Is it in QUICKSTART.md?
   - Check ARCHITECTURE.md for "how it works"

2. **Run diagnostic test:**
   ```bash
   python test.py
   ```
   Tells you exactly what's working/broken

3. **Enable debug logging:**
   ```
   LOG_LEVEL=DEBUG
   DEBUG_MODE=true
   ```
   in .env file

4. **Check the logs:**
   ```
   logs/scanner.log
   logs/dashboard.log
   logs/backtest.log
   ```

---

## 📝 Notes for Contributors

If improving the project:

1. **Update README.md** if changing user-facing features
2. **Update ARCHITECTURE.md** if changing code structure
3. **Update CHANGELOG.md** when releasing new version
4. **Update this INDEX.md** if adding new files/docs
5. **Add docstrings** to new functions
6. **Update config.py** documentation when adding settings

---

## 🎓 External Resources

- **MetaTrader5 Docs:** https://www.metatrader5.com/en/terminal/help
- **Python Docs:** https://docs.python.org/3/
- **Pandas Docs:** https://pandas.pydata.org/docs/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Forex Trading:** https://www.investopedia.com/forex/

---

## 📋 File Sizes & Complexity

| File | Lines | Complexity | Read Time |
|------|-------|-----------|-----------|
| config.py | 150 | Low | 10 min |
| mt5_connector.py | 250 | Medium | 20 min |
| scanner.py | 350 | High | 30 min |
| alerts.py | 300 | Medium | 20 min |
| data_processor.py | 300 | High | 25 min |
| utils.py | 200 | Low | 15 min |
| main.py | 200 | Medium | 15 min |
| dashboard/app.py | 400 | High | 30 min |
| backtest/backtest.py | 300 | High | 25 min |

---

## ✨ Quick Reference Cheat Sheet

```bash
# Setup
python setup.py                      # Initialize project
copy .env.example .env               # Create config

# Run
python main.py                       # Live scanner
streamlit run dashboard/app.py       # Web dashboard
python backtest/backtest.py          # Backtest
python test.py                       # Diagnostics

# Edit Configuration
.env                                 # Account settings
src/forex_scanner/config.py          # Scanner settings

# Check Status
python test.py                       # Run diagnostics
tail logs/scanner.log                # View live logs
```

---

**🎉 You're all set! Choose your starting point above and begin.**

*Last Updated: 2024-09-02*
*Forex Scanner v1.0.0*
