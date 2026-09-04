"""Deterministic synthetic observations for transparent demo mode."""
from datetime import datetime, timedelta
import hashlib
from .models import CURRENCIES, PAIRS

def stable(pair: str, low: float, high: float) -> float:
    raw = int(hashlib.sha256(pair.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return low + raw * (high - low)

def demo_market() -> dict:
    return {pair: {"price": stable(pair, 0.65, 190.0), "daily_change": stable(pair + "d", -1.25, 1.25), "source": "DEMO"} for pair in PAIRS}

def demo_currency() -> dict:
    return {currency: {"structural": round(stable(currency, -1.2, 1.2), 2), "repricing": round(stable(currency + "r", -2, 2), 2), "flow": round(stable(currency + "f", -1.5, 1.5), 2), "cot": None, "retail": None} for currency in CURRENCIES}

def demo_catalysts() -> list[dict]:
    now = datetime.utcnow()
    return [{"currency": "CAD", "event": "BoC guidance repricing", "timestamp": now - timedelta(hours=5), "importance": 5, "surprise": 0.8, "source": "DEMO"}, {"currency": "USD", "event": "Labor expectations", "timestamp": now - timedelta(hours=30), "importance": 4, "surprise": -0.4, "source": "DEMO"}, {"currency": "NZD", "event": "RBNZ cautious guidance", "timestamp": now - timedelta(days=2), "importance": 5, "surprise": -0.7, "source": "DEMO"}]


def yahoo_market(pairs: list[str]) -> tuple[dict, str]:
    """Build market snapshots from Yahoo, falling back pair-by-pair to demo data."""
    from data_sources.market_data import yahoo_snapshot
    snapshots = {}
    live_count = 0
    for pair in pairs:
        snapshot = yahoo_snapshot(pair)
        if snapshot["price"] is None:
            snapshot = demo_market()[pair]
        else:
            live_count += 1
        snapshots[pair] = snapshot
    return snapshots, "YAHOO FINANCE" if live_count else "DEMO"
