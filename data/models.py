"""Typed domain models used by the research terminal."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

PAIRS = ["EURUSD","GBPUSD","AUDUSD","NZDUSD","USDCAD","USDCHF","USDJPY","EURGBP","EURAUD","EURNZD","EURCAD","EURCHF","EURJPY","GBPAUD","GBPNZD","GBPCAD","GBPCHF","GBPJPY","AUDNZD","AUDCAD","AUDCHF","AUDJPY","NZDCAD","NZDCHF","NZDJPY","CADCHF","CADJPY","CHFJPY"]
CURRENCIES = ["USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"]

@dataclass
class DataPoint:
    value: Optional[float]
    source: str = "DEMO"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0
    status: str = "DEMO"

@dataclass
class PairAnalysis:
    pair: str
    price: Optional[float]
    daily_change: Optional[float]
    score: float
    bias: str
    confidence: float
    grade: str
    factors: dict[str, float]
    alignment: int
    catalyst: str
    action: str
    explanation: str
    contradictions: list[str] = field(default_factory=list)
