"""
MetaTrader5 Connector Module
Handles MT5 connection, data retrieval, and candle management
"""

import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
import pytz

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from src.forex_scanner.config import config

logger = logging.getLogger(__name__)


class MT5Connector:
    """Manages MetaTrader5 connection and data retrieval"""
    
    def __init__(self, account: Optional[int] = None, password: Optional[str] = None, 
                 server: Optional[str] = None):
        """
        Initialize MT5 Connector
        
        Args:
            account: MT5 account number
            password: MT5 password
            server: MT5 server name
        """
        self.account = account or config.MT5_ACCOUNT
        self.password = password or config.MT5_PASSWORD
        self.server = server or config.MT5_SERVER
        self.connected = False
        self.market_tz = config.market_tz
        
    def connect(self) -> bool:
        """
        Connect to MT5 terminal
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if mt5 is None:
            logger.error("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
            return False
            
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if account/password provided
            if self.account and self.password:
                if not mt5.login(self.account, self.password, self.server):
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self.connected = True
            account_info = mt5.account_info()
            logger.info(f"Connected to MT5 - Account: {account_info.login}, Balance: {account_info.balance}")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MT5"""
        if mt5 and self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def is_connected(self) -> bool:
        """Check if MT5 is connected"""
        if not mt5:
            return False
        return mt5.terminal_info() is not None
    
    def get_candles(self, symbol: str, timeframe: int = mt5.TIMEFRAME_H4 if mt5 else None,
                    count: int = 100, start_time: Optional[datetime] = None) -> Optional[list]:
        """
        Get OHLC candles from MT5
        
        Args:
            symbol: Currency pair (e.g., "EURUSD")
            timeframe: MT5 timeframe constant (default: 4-hour)
            count: Number of candles to retrieve
            start_time: Start time for candles (if None, get recent candles)
            
        Returns:
            List of candle tuples or None if error
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        try:
            if timeframe is None:
                timeframe = mt5.TIMEFRAME_H4
            
            # Get rates from MT5
            if start_time:
                rates = mt5.copy_rates_from(symbol, timeframe, start_time, count)
            else:
                rates = mt5.copy_rates_range(symbol, timeframe, 
                                            datetime.utcnow() - timedelta(days=100),
                                            datetime.utcnow())
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No candles retrieved for {symbol}")
                return None
            
            return rates
            
        except Exception as e:
            logger.error(f"Error retrieving candles for {symbol}: {e}")
            return None
    
    def get_latest_minute_candles(self, symbol: str, minutes: int = 60) -> Optional[list]:
        """
        Get latest 1-minute candles
        
        Args:
            symbol: Currency pair
            minutes: Number of recent minutes to retrieve
            
        Returns:
            List of 1-minute candles
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        try:
            timeframe = mt5.TIMEFRAME_M1 if mt5 else None
            if timeframe is None:
                return None
            
            rates = mt5.copy_rates_range(symbol, timeframe,
                                        datetime.utcnow() - timedelta(minutes=minutes),
                                        datetime.utcnow())
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No 1-minute candles retrieved for {symbol}")
                return None
            
            return rates
            
        except Exception as e:
            logger.error(f"Error retrieving minute candles for {symbol}: {e}")
            return None
    
    def get_bid_ask(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Get current bid/ask prices
        
        Args:
            symbol: Currency pair
            
        Returns:
            Tuple of (bid, ask) or None if error
        """
        if not self.is_connected():
            return None
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick.bid, tick.ask
            return None
        except Exception as e:
            logger.error(f"Error getting bid/ask for {symbol}: {e}")
            return None
    
    def convert_to_nairobi_time(self, utc_time: datetime) -> datetime:
        """Convert UTC time to Nairobi timezone"""
        utc = pytz.UTC
        utc_dt = utc.localize(utc_time)
        nairobi_dt = utc_dt.astimezone(self.market_tz)
        return nairobi_dt
    
    def convert_from_nairobi_time(self, nairobi_time: datetime) -> datetime:
        """Convert Nairobi time to UTC"""
        if nairobi_time.tzinfo is None:
            nairobi_time = self.market_tz.localize(nairobi_time)
        return nairobi_time.astimezone(pytz.UTC).replace(tzinfo=None)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information from MT5"""
        if not self.is_connected():
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info:
                return {
                    "name": info.name,
                    "bid": info.bid,
                    "ask": info.ask,
                    "point": info.point,
                    "digits": info.digits,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None


# Example usage functions
def test_connection():
    """Test MT5 connection"""
    connector = MT5Connector()
    if connector.connect():
        print("✓ Connected to MT5")
        info = connector.get_symbol_info("EURUSD")
        if info:
            print(f"✓ EURUSD: Bid={info['bid']}, Ask={info['ask']}")
        connector.disconnect()
    else:
        print("✗ Failed to connect to MT5")


if __name__ == "__main__":
    test_connection()
