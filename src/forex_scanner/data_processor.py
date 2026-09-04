"""
Data Processor Module
Handles data processing, backtesting, and historical analysis
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector
from src.forex_scanner.scanner import ForexScanner, LowSignal, BreakoutSignal

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and analyze forex data"""
    
    def __init__(self, mt5_connector: MT5Connector):
        """
        Initialize data processor
        
        Args:
            mt5_connector: Connected MT5Connector instance
        """
        self.mt5 = mt5_connector
        self.market_tz = config.market_tz
    
    def load_historical_data(self, pair: str, start_date: str, 
                            end_date: str) -> Optional[pd.DataFrame]:
        """
        Load historical 1-minute candle data for a pair.
        
        Args:
            pair: Currency pair
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with OHLC data or None if error
        """
        try:
            import MetaTrader5 as mt5
            
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Get rates
            rates = self.mt5.get_candles(
                pair, 
                timeframe=mt5.TIMEFRAME_M1,
                count=None,
                start_time=start
            )
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No historical data for {pair}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Filter by date range
            df = df[(df['time'] >= start) & (df['time'] <= end)].copy()
            
            if len(df) == 0:
                logger.warning(f"No data in date range for {pair}")
                return None
            
            logger.info(f"Loaded {len(df)} candles for {pair} ({start_date} to {end_date})")
            return df
            
        except Exception as e:
            logger.error(f"Error loading historical data for {pair}: {e}")
            return None
    
    def resample_to_4h_nairobi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample minute data to 4-hour candles aligned to Nairobi timezone.
        
        Args:
            df: DataFrame with minute candles
            
        Returns:
            DataFrame with 4-hour candles
        """
        try:
            df_copy = df.copy()
            
            # Convert to Nairobi timezone
            df_copy['time'] = pd.to_datetime(df_copy['time']).dt.tz_localize('UTC').dt.tz_convert(self.market_tz)
            
            # Group into 4-hour candles starting at 8:00 AM Nairobi time
            # Create a label for each 4H candle
            df_copy['day'] = df_copy['time'].dt.date
            df_copy['hour'] = df_copy['time'].dt.hour
            
            # Assign to 4H candle (8:00-12:00, 12:00-16:00, etc.)
            def get_4h_candle_start(hour):
                return (hour // 4) * 4
            
            df_copy['candle_hour'] = df_copy['hour'].apply(get_4h_candle_start)
            df_copy['candle_time'] = (df_copy['day'].astype(str) + ' ' + 
                                     df_copy['candle_hour'].astype(str).str.zfill(2) + ':00')
            df_copy['candle_time'] = pd.to_datetime(df_copy['candle_time']).dt.tz_localize(self.market_tz)
            
            # Resample OHLC
            df_4h = df_copy.groupby('candle_time').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'tick_volume': 'sum',
            }).reset_index()
            
            logger.info(f"Resampled {len(df_copy)} minute candles to {len(df_4h)} 4H candles")
            return df_4h
            
        except Exception as e:
            logger.error(f"Error resampling to 4H: {e}")
            return pd.DataFrame()
    
    def backtest_setup(self, pair: str, start_date: str, 
                      end_date: str) -> Dict:
        """
        Backtest the 8:00-12:00 4H setup for a pair over a date range.
        
        Args:
            pair: Currency pair
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with backtest results
        """
        try:
            logger.info(f"Starting backtest for {pair} ({start_date} to {end_date})")
            
            # Load data
            df = self.load_historical_data(pair, start_date, end_date)
            if df is None:
                return {"error": "Failed to load data"}
            
            # Convert to Nairobi time
            df['time_nairobi'] = pd.to_datetime(df['time']).dt.tz_localize('UTC').dt.tz_convert(self.market_tz)
            
            setup_count = 0
            breakout_count = 0
            profitable_count = 0
            losing_count = 0
            breakeven_count = 0
            
            results_details = []
            
            # Group by 4H candles (8:00-12:00)
            df['day'] = df['time_nairobi'].dt.date
            df['hour'] = df['time_nairobi'].dt.hour
            
            # Filter for 8:00-12:00 window
            df_8am_candles = df[(df['hour'] >= 8) & (df['hour'] < 12)].copy()
            
            # Group by day to find unique 8am candles
            for day, day_group in df_8am_candles.groupby('day'):
                day_group_sorted = day_group.sort_values('time')
                
                # Get 4H candle metrics
                candle_open = day_group_sorted.iloc[0]['open']
                candle_high = day_group_sorted['high'].max()
                candle_low = day_group_sorted['low'].min()
                candle_close = day_group_sorted.iloc[-1]['close']
                
                # Find if low was formed in late window (11:50-11:59)
                late_window = day_group_sorted[
                    (day_group_sorted['time_nairobi'].dt.hour == 11) &
                    (day_group_sorted['time_nairobi'].dt.minute >= config.LATE_LOW_THRESHOLD_MINUTES)
                ]
                
                if len(late_window) == 0:
                    continue  # No late low
                
                # Find the exact low time
                low_idx = day_group_sorted['low'].idxmin()
                low_price = day_group_sorted.loc[low_idx, 'low']
                low_time = day_group_sorted.loc[low_idx, 'time_nairobi']
                
                # Check if low was in late window
                if low_time.hour != 11 or low_time.minute < config.LATE_LOW_THRESHOLD_MINUTES:
                    continue
                
                setup_count += 1
                
                # Check next day's 12:00 candle for breakout
                next_day = day + timedelta(days=1)
                df_12pm = df[(df['day'] == next_day) & (df['hour'] == 12)].copy()
                
                if len(df_12pm) == 0:
                    continue
                
                # Get first 1-5 minutes of 12:00 candle
                df_12pm_sorted = df_12pm.sort_values('time').head(config.BREAKOUT_WATCH_WINDOW_MINUTES)
                min_in_window = df_12pm_sorted['low'].min()
                
                # Check if breakout occurred
                if min_in_window < low_price:
                    breakout_count += 1
                    
                    # Calculate P&L (simple: entry at low, target at 50% midpoint)
                    midpoint = candle_low + (candle_high - candle_low) * 0.5
                    entry_price = min_in_window
                    
                    # Get price move to target
                    pips = (midpoint - entry_price) * 100000  # Assuming 5 digit pair
                    
                    if pips > 0:
                        profitable_count += 1
                    elif pips < 0:
                        losing_count += 1
                    else:
                        breakeven_count += 1
                    
                    results_details.append({
                        "date": day,
                        "low_price": low_price,
                        "low_time": low_time,
                        "breakout_price": min_in_window,
                        "target": midpoint,
                        "pips": pips,
                        "profitable": pips > 0,
                    })
            
            # Calculate statistics
            win_rate = (profitable_count / breakout_count * 100) if breakout_count > 0 else 0
            setup_to_breakout_rate = (breakout_count / setup_count * 100) if setup_count > 0 else 0
            
            return {
                "pair": pair,
                "start_date": start_date,
                "end_date": end_date,
                "total_setups": setup_count,
                "total_breakouts": breakout_count,
                "profitable_trades": profitable_count,
                "losing_trades": losing_count,
                "breakeven_trades": breakeven_count,
                "win_rate_percent": win_rate,
                "setup_to_breakout_rate_percent": setup_to_breakout_rate,
                "details": results_details,
            }
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {"error": str(e)}
    
    def backtest_all_pairs(self, start_date: str, end_date: str) -> Dict[str, Dict]:
        """
        Backtest all configured pairs
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary of pair -> backtest results
        """
        results = {}
        
        for pair in config.FOREX_PAIRS:
            logger.info(f"Backtesting {pair}...")
            results[pair] = self.backtest_setup(pair, start_date, end_date)
        
        return results
    
    def save_backtest_results(self, results: Dict, filename: str = "backtest_results.csv"):
        """Save backtest results to CSV"""
        try:
            rows = []
            
            for pair, data in results.items():
                if "error" in data:
                    continue
                
                row = {
                    "Pair": pair,
                    "Period": f"{data['start_date']} to {data['end_date']}",
                    "Total Setups": data['total_setups'],
                    "Total Breakouts": data['total_breakouts'],
                    "Profitable": data['profitable_trades'],
                    "Losing": data['losing_trades'],
                    "Win Rate %": f"{data['win_rate_percent']:.1f}",
                    "Setup->Breakout %": f"{data['setup_to_breakout_rate_percent']:.1f}",
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False)
            logger.info(f"✓ Backtest results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving backtest results: {e}")
    
    def export_signal_details(self, results: Dict, filename: str = "signal_details.csv"):
        """Export detailed signal information to CSV"""
        try:
            all_details = []
            
            for pair, data in results.items():
                if "details" not in data:
                    continue
                
                for detail in data["details"]:
                    all_details.append({
                        "Pair": pair,
                        "Date": detail["date"],
                        "Low Price": detail["low_price"],
                        "Low Time": detail["low_time"],
                        "Breakout Price": detail["breakout_price"],
                        "Target": detail["target"],
                        "Pips": f"{detail['pips']:.1f}",
                        "Profitable": detail["profitable"],
                    })
            
            df = pd.DataFrame(all_details)
            df.to_csv(filename, index=False)
            logger.info(f"✓ Signal details exported to {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting signal details: {e}")
