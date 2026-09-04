"""
Core Scanner Logic Module
Detects 8:00-12:00 4H candle alignment setup and breakouts
"""

import logging
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pytz
import pandas as pd

from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector

logger = logging.getLogger(__name__)


@dataclass
class LowSignal:
    """Represents a detected low signal"""
    pair: str
    low_price: float
    low_time: datetime  # Nairobi time
    low_minute: int  # Minute within the 4H candle (0-240)
    candle_high: float
    candle_open: float
    candle_close: float
    midpoint_target: float  # 50% of candle range
    detected_at: datetime


@dataclass
class BreakoutSignal:
    """Represents a detected breakout signal"""
    pair: str
    low_signal: LowSignal
    breakout_price: float
    breakout_time: datetime  # Nairobi time
    breakout_minute_candle_time: datetime
    breakout_distance_pips: float
    signal_strength: str  # "STRONG", "MODERATE", "WEAK"
    ready_to_trade: bool


class ForexScanner:
    """Main scanner class for detecting 4-hour candle alignment setups"""
    
    def __init__(self, mt5_connector: MT5Connector):
        """
        Initialize the scanner
        
        Args:
            mt5_connector: Connected MT5Connector instance
        """
        self.mt5 = mt5_connector
        self.market_tz = config.market_tz
        self.low_signals: Dict[str, LowSignal] = {}  # pair -> LowSignal
        self.active_breakout_watches: Dict[str, LowSignal] = {}  # pair -> LowSignal being watched
        
    def get_nairobi_time(self) -> datetime:
        """Get current time in Nairobi timezone"""
        utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        return utc_now.astimezone(self.market_tz).replace(tzinfo=None)
    
    def get_current_minute_of_4h_candle(self) -> int:
        """
        Get which minute of the current 4-hour candle we're in.
        E.g., 8:00 = 0, 8:01 = 1, ..., 11:59 = 239
        
        Returns:
            int: Minutes since 8:00 AM (0-239)
        """
        now = self.get_nairobi_time()
        candle_start = now.replace(hour=config.CANDLE_START_HOUR, minute=0, second=0, microsecond=0)
        minutes_elapsed = int((now - candle_start).total_seconds() / 60)
        return max(0, min(239, minutes_elapsed))  # Clamp to 0-239
    
    def get_4h_candle_for_time(self, time: datetime) -> Tuple[datetime, datetime]:
        """
        Get the start and end time of the 4-hour candle containing this time.
        
        Args:
            time: Datetime to get candle for
            
        Returns:
            Tuple of (candle_start, candle_end) in Nairobi time
        """
        start = time.replace(hour=config.CANDLE_START_HOUR, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=4)
        return start, end
    
    def is_in_target_4h_candle(self, time: datetime) -> bool:
        """
        Check if time is within the target 8:00-12:00 4H candle.
        
        Args:
            time: Time to check (Nairobi timezone)
            
        Returns:
            bool: True if within the candle
        """
        return config.CANDLE_START_HOUR <= time.hour < config.CANDLE_END_HOUR
    
    def is_late_low_time(self, time: datetime) -> bool:
        """
        Check if time is within the late-low detection window (after 11:50).
        
        Args:
            time: Time to check (Nairobi timezone)
            
        Returns:
            bool: True if late enough in the candle
        """
        return (time.hour == 11 and 
                time.minute >= config.LATE_LOW_THRESHOLD_MINUTES)
    
    def scan_4h_candle(self, pair: str) -> Optional[LowSignal]:
        """
        Scan the current/recent 4H candle for the 8:00-12:00 setup.
        
        Strategy:
        1. Get the 4H candle that contains the current time
        2. Check if a low was formed between 11:50-11:59
        3. Calculate the midpoint target (50% of candle)
        4. Return LowSignal if conditions met
        
        Args:
            pair: Currency pair (e.g., "EURUSD")
            
        Returns:
            LowSignal if setup detected, None otherwise
        """
        try:
            # Import MT5 if needed
            try:
                import MetaTrader5 as mt5
            except ImportError:
                logger.error("MetaTrader5 not installed")
                return None
            
            # Get current 4H candle
            now = self.get_nairobi_time()
            candle_start, candle_end = self.get_4h_candle_for_time(now)
            
            logger.debug(f"Scanning {pair}: 4H candle {candle_start} to {candle_end}")
            
            # Fetch 1-minute candles for this period
            candles = self.mt5.get_candles(pair, timeframe=mt5.TIMEFRAME_M1, count=300)
            
            if candles is None or len(candles) == 0:
                logger.warning(f"No candles available for {pair}")
                return None
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(candles)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Convert to Nairobi time
            df['time_nairobi'] = df['time'].dt.tz_localize('UTC').dt.tz_convert(self.market_tz)
            
            # Filter for 8:00-12:00 window
            df['hour'] = df['time_nairobi'].dt.hour
            df_window = df[(df['hour'] >= config.CANDLE_START_HOUR) & 
                          (df['hour'] < config.CANDLE_END_HOUR)].copy()
            
            if len(df_window) == 0:
                logger.debug(f"No candles in 8:00-12:00 window for {pair}")
                return None
            
            # Get 4H candle OHLC
            candle_open = df_window.iloc[0]['open']
            candle_high = df_window['high'].max()
            candle_low = df_window['low'].min()
            candle_close = df_window.iloc[-1]['close']
            
            # Find the minute where the low was formed
            low_idx = df_window['low'].idxmin()
            low_time_nairobi = df_window.loc[low_idx, 'time_nairobi'].to_pydatetime()
            
            # Calculate minutes into the 4H candle (0-240)
            minutes_into_candle = int((low_time_nairobi - candle_start).total_seconds() / 60)
            
            # Check if low was formed in late window (11:50-11:59 = minutes 230-239)
            is_late_low = (low_time_nairobi.hour == 11 and 
                          low_time_nairobi.minute >= config.LATE_LOW_THRESHOLD_MINUTES)
            
            if not is_late_low:
                logger.debug(f"{pair}: Low formed too early at {low_time_nairobi.strftime('%H:%M')}")
                return None
            
            # Calculate 50% midpoint of the candle range
            candle_range = candle_high - candle_low
            midpoint = candle_low + (candle_range * 0.5)
            
            # Create and return the signal
            signal = LowSignal(
                pair=pair,
                low_price=float(df_window.loc[low_idx, 'low']),
                low_time=low_time_nairobi,
                low_minute=minutes_into_candle,
                candle_high=float(candle_high),
                candle_open=float(candle_open),
                candle_close=float(candle_close),
                midpoint_target=float(midpoint),
                detected_at=datetime.now()
            )
            
            logger.info(f"✓ {pair}: Late 8am 4H low detected at {signal.low_time.strftime('%H:%M')} "
                       f"({signal.low_price}), Target: {signal.midpoint_target}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error scanning {pair}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def check_12pm_breakout(self, pair: str, low_signal: LowSignal) -> Optional[BreakoutSignal]:
        """
        Monitor for 12:00 4H candle breakout within first 1-5 minutes.
        Check if price takes out (breaks below) the 11:59 low.
        
        Args:
            pair: Currency pair
            low_signal: The LowSignal detected in the 8am candle
            
        Returns:
            BreakoutSignal if breakout detected, None otherwise
        """
        try:
            import MetaTrader5 as mt5
        except ImportError:
            logger.error("MetaTrader5 not installed")
            return None
        
        try:
            now = self.get_nairobi_time()
            
            # Check if we're in the 12:00 candle
            if now.hour != 12:
                logger.debug(f"{pair}: Not in 12:00 hour yet")
                return None
            
            # Check if we're within the breakout watch window (first 1-5 minutes)
            if now.minute > config.BREAKOUT_WATCH_WINDOW_MINUTES:
                logger.debug(f"{pair}: Outside breakout watch window ({now.minute} > {config.BREAKOUT_WATCH_WINDOW_MINUTES})")
                return None
            
            # Get 1-minute candles for the 12:00 hour
            candles = self.mt5.get_candles(pair, timeframe=mt5.TIMEFRAME_M1, count=60)
            
            if candles is None or len(candles) == 0:
                logger.warning(f"No minute candles available for {pair}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df['time_nairobi'] = df['time'].dt.tz_localize('UTC').dt.tz_convert(self.market_tz)
            
            # Filter for 12:00 hour
            df['hour'] = df['time_nairobi'].dt.hour
            df_12pm = df[df['hour'] == 12].copy()
            
            if len(df_12pm) == 0:
                logger.debug(f"{pair}: No 12:00 hour candles yet")
                return None
            
            # Get minimum low in the breakout window
            min_low = df_12pm['low'].min()
            min_low_idx = df_12pm['low'].idxmin()
            breakout_time = df_12pm.loc[min_low_idx, 'time_nairobi'].to_pydatetime()
            
            # Check if low was taken out (price went below the 11:59 low)
            if min_low < low_signal.low_price:
                # Calculate breakout distance in pips
                symbol_info = self.mt5.get_symbol_info(pair)
                digits = symbol_info['digits'] if symbol_info else 5
                breakout_distance_pips = abs(min_low - low_signal.low_price) * (10 ** digits)
                
                # Determine signal strength based on how far below the low we went
                if breakout_distance_pips < 5:
                    signal_strength = "WEAK"
                elif breakout_distance_pips < 15:
                    signal_strength = "MODERATE"
                else:
                    signal_strength = "STRONG"
                
                breakout_signal = BreakoutSignal(
                    pair=pair,
                    low_signal=low_signal,
                    breakout_price=float(min_low),
                    breakout_time=breakout_time,
                    breakout_minute_candle_time=breakout_time,
                    breakout_distance_pips=float(breakout_distance_pips),
                    signal_strength=signal_strength,
                    ready_to_trade=True
                )
                
                logger.info(f"✓ {pair}: 12pm BREAKOUT DETECTED! "
                           f"Low={low_signal.low_price}, Breakout={min_low} ({signal_strength})")
                
                return breakout_signal
            else:
                logger.debug(f"{pair}: No breakout yet (min={min_low}, signal_low={low_signal.low_price})")
                return None
                
        except Exception as e:
            logger.error(f"Error checking breakout for {pair}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def scan_all_pairs(self) -> Dict[str, Optional[LowSignal]]:
        """
        Scan all configured pairs for 8am 4H setup.
        
        Returns:
            Dictionary of pair -> LowSignal (or None if not found)
        """
        results = {}
        for pair in config.FOREX_PAIRS:
            signal = self.scan_4h_candle(pair)
            results[pair] = signal
            if signal:
                self.active_breakout_watches[pair] = signal
        
        return results
    
    def check_all_breakouts(self) -> List[BreakoutSignal]:
        """
        Check all active low signals for 12pm breakout.
        
        Returns:
            List of detected BreakoutSignals
        """
        breakout_signals = []
        for pair, low_signal in self.active_breakout_watches.items():
            breakout = self.check_12pm_breakout(pair, low_signal)
            if breakout:
                breakout_signals.append(breakout)
                # Clean up after trade signal
                del self.active_breakout_watches[pair]
        
        return breakout_signals
    
    def get_statistics(self) -> Dict:
        """Get scanning statistics"""
        return {
            "pairs_monitored": len(config.FOREX_PAIRS),
            "active_low_signals": len(self.active_breakout_watches),
            "candle_start_hour": config.CANDLE_START_HOUR,
            "candle_end_hour": config.CANDLE_END_HOUR,
            "late_low_threshold_minutes": config.LATE_LOW_THRESHOLD_MINUTES,
            "breakout_watch_window_minutes": config.BREAKOUT_WATCH_WINDOW_MINUTES,
        }
