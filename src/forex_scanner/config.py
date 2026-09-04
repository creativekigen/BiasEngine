"""
Configuration management for Forex Scanner
Handles timezone, pairs, alert settings, and MT5 connection params
"""

import os
from enum import Enum
from typing import List, Dict
from pydantic_settings import BaseSettings
import pytz


class AlertType(str, Enum):
    """Supported alert types"""
    CONSOLE = "console"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SOUND = "sound"


class Config(BaseSettings):
    """Main configuration class"""

    # ===== MARKET DATA =====
    # Timezone settings
    MARKET_TIMEZONE: str = "Africa/Nairobi"  # Broker/monitor timezone
    UTC_OFFSET_HOURS: int = 3  # East Africa Time (EAT)
    
    # MT5 Connection
    MT5_ACCOUNT: int = int(os.getenv("MT5_ACCOUNT", "0"))
    MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER: str = os.getenv("MT5_SERVER", "JustMarkets-Server")
    
    # ===== SCANNER SETUP =====
    # Target 4H candle: 8:00-12:00 Nairobi time
    CANDLE_START_HOUR: int = 8  # 8:00 AM
    CANDLE_END_HOUR: int = 12   # 12:00 PM (noon)
    
    # Low detection parameters
    LATE_LOW_MINUTES: int = 10  # Low must form after 11:50 (within last 10 min)
    LATE_LOW_THRESHOLD_MINUTES: int = 50  # Latest minute where low can form (11:50)
    
    # Breakout detection after 12:00
    BREAKOUT_WATCH_WINDOW_MINUTES: int = 5  # Check first 1-5 minutes after 12:00
    BREAKOUT_TIMEFRAME: str = "1min"  # Use 1-minute candles for breakout detection
    
    # ===== FOREX PAIRS =====
    # 28 Major and Minor Currency Pairs
    FOREX_PAIRS: List[str] = [
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
    
    # Remove duplicates
    FOREX_PAIRS: List[str] = list(set(FOREX_PAIRS))
    
    # ===== ALERT SETTINGS =====
    ALERT_TYPES: List[AlertType] = [
        AlertType.CONSOLE,
        AlertType.SOUND,
    ]
    
    # Telegram Bot Settings
    TELEGRAM_ENABLED: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Discord Webhook Settings
    DISCORD_ENABLED: bool = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Email Settings
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_SMTP_SERVER: str = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_RECIPIENT: str = os.getenv("EMAIL_RECIPIENT", "")
    
    # Sound Alert
    SOUND_ENABLED: bool = True
    SOUND_FILE: str = os.getenv("SOUND_FILE", "alert.wav")
    
    # ===== LOGGING & DEBUG =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # ===== BACKTEST =====
    BACKTEST_START_DATE: str = "2024-01-01"
    BACKTEST_END_DATE: str = "2024-12-31"
    
    class Config:
        case_sensitive = False
        env_file = ".env"
        
    @property
    def market_tz(self):
        """Get pytz timezone object"""
        return pytz.timezone(self.MARKET_TIMEZONE)
    
    def get_high_low_filter(self) -> Dict:
        """Return high/low filter settings for late low detection"""
        return {
            "late_low_minutes": self.LATE_LOW_MINUTES,
            "late_low_threshold_minutes": self.LATE_LOW_THRESHOLD_MINUTES,
        }
    
    def get_breakout_filter(self) -> Dict:
        """Return breakout detection settings"""
        return {
            "watch_window_minutes": self.BREAKOUT_WATCH_WINDOW_MINUTES,
            "timeframe": self.BREAKOUT_TIMEFRAME,
        }


# Create a singleton config instance
config = Config()
