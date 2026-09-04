"""SQLite persistence for observations and generated signals."""
import sqlite3
from pathlib import Path
from typing import Iterable

TABLES = {
    "market_data": "(id INTEGER PRIMARY KEY, symbol TEXT, value REAL, timestamp TEXT, source TEXT)",
    "economic_events": "(id INTEGER PRIMARY KEY, currency TEXT, event TEXT, actual REAL, forecast REAL, previous REAL, timestamp TEXT, source TEXT)",
    "central_bank_events": "(id INTEGER PRIMARY KEY, currency TEXT, bank TEXT, guidance REAL, timestamp TEXT, source TEXT)",
    "yield_data": "(id INTEGER PRIMARY KEY, currency TEXT, tenor TEXT, value REAL, previous REAL, driver TEXT, timestamp TEXT, source TEXT)",
    "commodity_data": "(id INTEGER PRIMARY KEY, asset TEXT, value REAL, change REAL, timestamp TEXT, source TEXT)",
    "cot_data": "(id INTEGER PRIMARY KEY, currency TEXT, net_position REAL, weekly_change REAL, timestamp TEXT, source TEXT)",
    "retail_sentiment": "(id INTEGER PRIMARY KEY, pair TEXT, long_pct REAL, short_pct REAL, timestamp TEXT, source TEXT)",
    "news_events": "(id INTEGER PRIMARY KEY, currency TEXT, headline TEXT, importance INTEGER, timestamp TEXT, source TEXT)",
    "pair_scores": "(id INTEGER PRIMARY KEY, pair TEXT, score REAL, confidence REAL, grade TEXT, timestamp TEXT)",
    "signals": "(id INTEGER PRIMARY KEY, pair TEXT, direction TEXT, score REAL, confidence REAL, timestamp TEXT)",
    "trade_results": "(id INTEGER PRIMARY KEY, pair TEXT, direction TEXT, entry REAL, outcome REAL, r_multiple REAL, timestamp TEXT)",
    "system_logs": "(id INTEGER PRIMARY KEY, level TEXT, message TEXT, timestamp TEXT)",
}

def init_db(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        for name, schema in TABLES.items():
            conn.execute(f"CREATE TABLE IF NOT EXISTS {name} {schema}")
        conn.commit()

def save_scores(path: str, analyses: Iterable) -> None:
    with sqlite3.connect(path) as conn:
        conn.executemany("INSERT INTO pair_scores(pair, score, confidence, grade, timestamp) VALUES (?, ?, ?, ?, datetime('now'))", [(a.pair, a.score, a.confidence, a.grade) for a in analyses])
        conn.commit()
