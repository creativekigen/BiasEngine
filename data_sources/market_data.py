"""Market data providers, including a Yahoo Finance fallback."""
from datetime import datetime
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def history(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame: ...


def yahoo_symbol(pair: str) -> str:
    """Convert an FX pair into Yahoo Finance's forex symbol format."""
    return f"{pair}=X"


def yahoo_history(pair: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical FX prices from Yahoo Finance; return empty data on failure."""
    return yahoo_history_symbol(yahoo_symbol(pair), period=period, interval=interval)


def yahoo_history_symbol(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch a Yahoo Finance instrument history by its native ticker symbol."""
    try:
        import yfinance as yf
        history = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if isinstance(history.columns, pd.MultiIndex):
            history.columns = history.columns.get_level_values(0)
        return history.dropna(how="all")
    except Exception:
        return pd.DataFrame()


def yahoo_correlation_prices(period: str = "1y") -> dict[str, pd.Series]:
    """Return daily closing prices for FX pairs and major cross-asset benchmarks."""
    symbols = {pair: yahoo_symbol(pair) for pair in ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD")}
    symbols.update({"GOLD": "GC=F", "WTI": "CL=F", "S&P 500": "^GSPC"})
    prices = {}
    for name, symbol in symbols.items():
        history = yahoo_history_symbol(symbol, period=period)
        if not history.empty and "Close" in history:
            prices[name] = history["Close"].astype(float).dropna()
    return prices


def yahoo_snapshot(pair: str) -> dict:
    """Return a current/previous close snapshot with source metadata."""
    history = yahoo_history(pair, period="5d")
    if history.empty or "Close" not in history:
        return {"price": None, "daily_change": None, "source": "UNAVAILABLE", "timestamp": datetime.utcnow()}
    close = history["Close"].astype(float).dropna()
    price = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) > 1 else price
    return {"price": price, "daily_change": (price / previous - 1) * 100, "source": "YAHOO FINANCE", "timestamp": history.index[-1].to_pydatetime()}
