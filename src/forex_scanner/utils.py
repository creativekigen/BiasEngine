"""
Utility Functions Module
Helper functions for logging, timezone, and data formatting
"""

import logging
import logging.handlers
from typing import Optional
from datetime import datetime
from pathlib import Path
import pytz

from src.forex_scanner.config import config


def setup_logging(log_file: Optional[str] = "forex_scanner.log", 
                 level: str = None) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        log_file: Path to log file (None to disable file logging)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    log_level = level or config.LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to {log_file}")
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    return logger


def format_price(price: float, digits: int = 5) -> str:
    """Format price with appropriate decimal places"""
    return f"{price:.{digits}f}"


def format_pips(pips: float) -> str:
    """Format pips with 1 decimal place"""
    return f"{pips:.1f}"


def get_nairobi_time() -> datetime:
    """Get current time in Nairobi timezone"""
    utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    return utc_now.astimezone(config.market_tz).replace(tzinfo=None)


def get_utc_time() -> datetime:
    """Get current UTC time"""
    return datetime.utcnow()


def time_to_nairobi(utc_time: datetime) -> datetime:
    """Convert UTC time to Nairobi timezone"""
    if utc_time.tzinfo is None:
        utc_time = pytz.UTC.localize(utc_time)
    return utc_time.astimezone(config.market_tz).replace(tzinfo=None)


def time_to_utc(nairobi_time: datetime) -> datetime:
    """Convert Nairobi time to UTC"""
    if nairobi_time.tzinfo is None:
        nairobi_time = config.market_tz.localize(nairobi_time)
    return nairobi_time.astimezone(pytz.UTC).replace(tzinfo=None)


def is_market_open() -> bool:
    """Check if forex market is open"""
    now = get_nairobi_time()
    # Forex market is open 24/5, closed on weekends
    return now.weekday() < 4 or (now.weekday() == 4 and now.hour < 22)


def get_time_until_8am() -> int:
    """Get minutes until next 8am 4H candle"""
    now = get_nairobi_time()
    
    if now.hour < 8:
        next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
    else:
        from datetime import timedelta
        next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    minutes = int((next_8am - now).total_seconds() / 60)
    return max(0, minutes)


def get_time_until_12pm() -> int:
    """Get minutes until next 12pm 4H candle"""
    now = get_nairobi_time()
    
    if now.hour < 12:
        next_12pm = now.replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        from datetime import timedelta
        next_12pm = now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    minutes = int((next_12pm - now).total_seconds() / 60)
    return max(0, minutes)


def get_4h_candle_info() -> dict:
    """Get information about current 4H candle"""
    now = get_nairobi_time()
    
    # Current 4H candle starts at 8:00
    candle_start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    candle_end = candle_start.replace(hour=12)
    
    minutes_elapsed = int((now - candle_start).total_seconds() / 60)
    
    if minutes_elapsed < 0:
        from datetime import timedelta
        candle_start -= timedelta(days=1)
        candle_end -= timedelta(days=1)
        minutes_elapsed = int((now - candle_start).total_seconds() / 60)
    
    return {
        "candle_start": candle_start,
        "candle_end": candle_end,
        "minutes_elapsed": max(0, min(239, minutes_elapsed)),
        "minutes_remaining": max(0, 239 - minutes_elapsed),
        "percentage_complete": min(100, (minutes_elapsed / 240) * 100),
    }


def format_time_remaining(minutes: int) -> str:
    """Format minutes as HH:MM"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


class ScannerStats:
    """Utility class for tracking scanner statistics"""
    
    def __init__(self):
        self.total_scans = 0
        self.total_setups_detected = 0
        self.total_breakouts_detected = 0
        self.pairs_scanned = 0
        self.last_scan_time = None
        self.last_alert_time = None
    
    def record_scan(self, pairs_scanned: int, setups_detected: int, 
                   breakouts_detected: int):
        """Record scan statistics"""
        self.total_scans += 1
        self.pairs_scanned = pairs_scanned
        self.total_setups_detected += setups_detected
        self.total_breakouts_detected += breakouts_detected
        self.last_scan_time = datetime.now()
    
    def record_alert(self):
        """Record alert sent"""
        self.last_alert_time = datetime.now()
    
    def get_stats(self) -> dict:
        """Get statistics dictionary"""
        return {
            "total_scans": self.total_scans,
            "total_setups_detected": self.total_setups_detected,
            "total_breakouts_detected": self.total_breakouts_detected,
            "last_scan_time": self.last_scan_time.strftime("%H:%M:%S") if self.last_scan_time else None,
            "last_alert_time": self.last_alert_time.strftime("%H:%M:%S") if self.last_alert_time else None,
            "pairs_scanned": self.pairs_scanned,
        }


# Global stats instance
_stats = ScannerStats()


def get_stats() -> ScannerStats:
    """Get global scanner stats"""
    return _stats


def record_scan(pairs_scanned: int, setups_detected: int, breakouts_detected: int):
    """Record a scan"""
    _stats.record_scan(pairs_scanned, setups_detected, breakouts_detected)


def record_alert():
    """Record an alert sent"""
    _stats.record_alert()
