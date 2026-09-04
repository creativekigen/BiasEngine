"""
Main entry point for live Forex Scanner
Continuous monitoring mode with real-time alerts
"""

import logging
import time
import schedule
from datetime import datetime, timedelta
from typing import Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector
from src.forex_scanner.scanner import ForexScanner
from src.forex_scanner.alerts import get_alert_manager
from src.forex_scanner.utils import (
    setup_logging, get_nairobi_time, get_4h_candle_info,
    record_scan, record_alert, get_stats
)

# Setup logging
logger = setup_logging(log_file="logs/scanner.log", level="INFO")


class LiveScanner:
    """Live scanner with continuous monitoring and alerting"""
    
    def __init__(self):
        """Initialize live scanner"""
        self.mt5 = None
        self.scanner = None
        self.alert_manager = get_alert_manager()
        self.running = False
        
        logger.info("="*80)
        logger.info("Forex Scanner - Live Monitor Initialized")
        logger.info(f"Timezone: {config.MARKET_TIMEZONE}")
        logger.info(f"Pairs to monitor: {len(config.FOREX_PAIRS)}")
        logger.info(f"Candle window: {config.CANDLE_START_HOUR}:00-{config.CANDLE_END_HOUR}:00")
        logger.info("="*80)
    
    def connect(self) -> bool:
        """Connect to MT5 and initialize scanner"""
        try:
            logger.info("Connecting to MetaTrader5...")
            self.mt5 = MT5Connector()
            
            if not self.mt5.connect():
                logger.error("Failed to connect to MT5")
                return False
            
            logger.info("✓ Connected to MT5")
            
            # Initialize scanner
            self.scanner = ForexScanner(self.mt5)
            logger.info("✓ Scanner initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.mt5:
            self.mt5.disconnect()
            logger.info("Disconnected from MT5")
    
    def scan_setup(self):
        """Scan all pairs for 8am 4H setup"""
        try:
            now = get_nairobi_time()
            candle_info = get_4h_candle_info()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"SCAN - {now.strftime('%Y-%m-%d %H:%M:%S')} | "
                       f"Candle: {candle_info['percentage_complete']:.0f}% complete")
            logger.info(f"{'='*80}")
            
            if not self.scanner:
                logger.warning("Scanner not initialized")
                return
            
            # Scan all pairs
            results = self.scanner.scan_all_pairs()
            setups = {k: v for k, v in results.items() if v is not None}
            
            if setups:
                logger.info(f"✓ Found {len(setups)} late 8am 4H lows:")
                for pair, signal in setups.items():
                    logger.info(f"  • {pair}: Low={signal.low_price:.5f} at {signal.low_time.strftime('%H:%M')}")
                    
                    # Send alert for setup
                    if self.alert_manager.send_low_signal_alert(signal):
                        record_alert()
            else:
                logger.debug("No setups detected in this scan")
            
            # Record statistics
            record_scan(len(config.FOREX_PAIRS), len(setups), 0)
            
        except Exception as e:
            logger.error(f"Scan error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def check_breakouts(self):
        """Check for 12pm breakouts"""
        try:
            now = get_nairobi_time()
            
            if now.hour != 12:
                return  # Only check during 12:00 hour
            
            if now.minute > config.BREAKOUT_WATCH_WINDOW_MINUTES:
                return  # Outside watch window
            
            logger.info(f"Checking for 12:00 breakouts ({now.strftime('%H:%M:%S')})...")
            
            if not self.scanner:
                return
            
            # Check all active signals for breakout
            breakouts = self.scanner.check_all_breakouts()
            
            if breakouts:
                logger.warning(f"\n🚀 {len(breakouts)} BREAKOUT(S) DETECTED! 🚀\n")
                
                for breakout in breakouts:
                    logger.warning(
                        f"  {breakout.pair}: "
                        f"Low={breakout.low_signal.low_price:.5f} "
                        f"Breakout={breakout.breakout_price:.5f} "
                        f"({breakout.signal_strength}) - "
                        f"Target={breakout.low_signal.midpoint_target:.5f}"
                    )
                    
                    # Send breakout alert
                    if self.alert_manager.send_breakout_alert(breakout):
                        record_alert()
            
        except Exception as e:
            logger.error(f"Breakout check error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def print_status(self):
        """Print current scanner status"""
        try:
            now = get_nairobi_time()
            candle_info = get_4h_candle_info()
            stats = get_stats().get_stats()
            
            status_lines = [
                f"\n{'='*80}",
                f"STATUS - {now.strftime('%H:%M:%S')} ({config.MARKET_TIMEZONE})",
                f"{'='*80}",
                f"8am Candle Progress: {candle_info['percentage_complete']:.0f}% "
                f"({candle_info['minutes_elapsed']}/{candle_info['minutes_elapsed'] + candle_info['minutes_remaining']} min)",
                f"",
                f"Active Low Signals: {len(self.scanner.active_breakout_watches) if self.scanner else 0}",
                f"Total Scans: {stats['total_scans']}",
                f"Total Setups Found: {stats['total_setups_detected']}",
                f"Total Breakouts Found: {stats['total_breakouts_detected']}",
                f"",
                f"Next Scan: In ~{get_next_scan_minutes()} minutes",
                f"{'='*80}\n",
            ]
            
            logger.info("\n".join(status_lines))
            
        except Exception as e:
            logger.error(f"Status error: {e}")
    
    def schedule_jobs(self):
        """Schedule scanning jobs"""
        # Scan every 5 minutes during candle hours
        schedule.every(5).minutes.do(self.scan_setup)
        
        # Check breakouts every minute during 12:00 hour
        schedule.every(1).minute.do(self.check_breakouts)
        
        # Print status every 30 minutes
        schedule.every(30).minutes.do(self.print_status)
        
        logger.info("✓ Scan jobs scheduled")
    
    def run(self):
        """Run the live scanner"""
        try:
            self.running = True
            logger.info("Starting live scanner...")
            
            # Print initial status
            self.print_status()
            
            # Run scheduled jobs
            while self.running:
                try:
                    # Run pending jobs
                    schedule.run_pending()
                    
                    # Sleep to avoid busy-waiting
                    time.sleep(10)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"Job execution error: {e}")
                    time.sleep(30)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scanner"""
        self.running = False
        self.disconnect()
        logger.info("✓ Scanner stopped")


def get_next_scan_minutes() -> int:
    """Get minutes until next scan"""
    now = get_nairobi_time()
    next_scan = now + timedelta(minutes=5)
    minutes = int((next_scan - now).total_seconds() / 60)
    return max(1, minutes)


def main():
    """Main entry point"""
    scanner = LiveScanner()
    
    # Connect to MT5
    if not scanner.connect():
        logger.error("Failed to initialize scanner")
        return 1
    
    # Schedule jobs
    scanner.schedule_jobs()
    
    # Run
    try:
        scanner.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
