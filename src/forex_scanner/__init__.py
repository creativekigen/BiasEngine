"""
Forex Scanner - Multi-pair 4-hour candle alignment detector
Detects late 8am candle lows and monitors 12pm breakouts
"""

__version__ = "1.0.0"
__author__ = "Forex Scanner Team"

from src.forex_scanner.config import Config
from src.forex_scanner.mt5_connector import MT5Connector
from src.forex_scanner.scanner import ForexScanner

__all__ = ["Config", "MT5Connector", "ForexScanner"]
