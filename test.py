"""
Test Script for Forex Scanner
Diagnoses connection and configuration issues
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.forex_scanner.utils import setup_logging
from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector

# Setup logging
logger = setup_logging(log_file=None, level="INFO")


def test_configuration():
    """Test configuration loading"""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: Configuration Loading")
    logger.info("="*70)
    
    try:
        logger.info(f"✓ Market Timezone: {config.MARKET_TIMEZONE}")
        logger.info(f"✓ Candle Window: {config.CANDLE_START_HOUR}:00-{config.CANDLE_END_HOUR}:00")
        logger.info(f"✓ Late Low Threshold: {config.LATE_LOW_THRESHOLD_MINUTES} minutes")
        logger.info(f"✓ Breakout Watch Window: {config.BREAKOUT_WATCH_WINDOW_MINUTES} minutes")
        logger.info(f"✓ Total Pairs Configured: {len(config.FOREX_PAIRS)}")
        logger.info(f"✓ Sample Pairs: {', '.join(config.FOREX_PAIRS[:5])}")
        logger.info("\n✓ Configuration loaded successfully!")
        return True
    except Exception as e:
        logger.error(f"\n✗ Configuration error: {e}")
        return False


def test_mt5_connection():
    """Test MetaTrader5 connection"""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: MetaTrader5 Connection")
    logger.info("="*70)
    
    try:
        logger.info("Attempting to connect to MetaTrader5...")
        logger.info("(Ensure MT5 terminal is running and you're logged in)")
        
        mt5 = MT5Connector()
        
        if mt5.connect():
            logger.info("✓ Successfully connected to MT5!")
            
            # Try to get symbol info
            logger.info("\nTesting symbol retrieval...")
            for pair in ["EURUSD", "GBPUSD", "USDJPY"]:
                info = mt5.get_symbol_info(pair)
                if info:
                    logger.info(f"  ✓ {pair}: Bid={info['bid']}, Ask={info['ask']}")
                else:
                    logger.warning(f"  ⚠ {pair}: Could not retrieve (may not be in market watch)")
            
            mt5.disconnect()
            logger.info("\n✓ MT5 connection test passed!")
            return True
        else:
            logger.error("\n✗ Failed to connect to MetaTrader5")
            logger.error("Make sure:")
            logger.error("  1. MetaTrader5 desktop terminal is running")
            logger.error("  2. You are logged into your broker account")
            logger.error("  3. Your account number and password in .env are correct")
            return False
    
    except ImportError:
        logger.error("\n✗ MetaTrader5 package not installed")
        logger.error("Install with: pip install MetaTrader5")
        return False
    except Exception as e:
        logger.error(f"\n✗ MT5 connection error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def test_alerts():
    """Test alert configuration"""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: Alert Configuration")
    logger.info("="*70)
    
    try:
        from src.forex_scanner.alerts import get_alert_manager
        
        alert_manager = get_alert_manager()
        status = alert_manager.get_status()
        
        logger.info(f"Total Alert Channels: {status['total_channels']}")
        logger.info(f"Available Channels: {', '.join(status['available_channels'])}")
        
        # Check each channel
        if status['console_enabled']:
            logger.info("  ✓ Console alerts: ENABLED")
        else:
            logger.info("  ✗ Console alerts: DISABLED")
        
        if status['telegram_enabled']:
            logger.info("  ✓ Telegram alerts: ENABLED")
        else:
            logger.info("  ⚠ Telegram alerts: DISABLED (not configured in .env)")
        
        if status['discord_enabled']:
            logger.info("  ✓ Discord alerts: ENABLED")
        else:
            logger.info("  ⚠ Discord alerts: DISABLED (not configured in .env)")
        
        if status['email_enabled']:
            logger.info("  ✓ Email alerts: ENABLED")
        else:
            logger.info("  ⚠ Email alerts: DISABLED (not configured in .env)")
        
        if status['sound_enabled']:
            logger.info("  ✓ Sound alerts: ENABLED")
        else:
            logger.info("  ⚠ Sound alerts: DISABLED")
        
        logger.info("\n✓ Alert configuration check complete!")
        return True
    
    except Exception as e:
        logger.error(f"\n✗ Alert configuration error: {e}")
        return False


def test_data_processing():
    """Test data processing capabilities"""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: Data Processing")
    logger.info("="*70)
    
    try:
        import pandas as pd
        import numpy as np
        
        # Test basic data operations
        logger.info("Testing Pandas/NumPy functionality...")
        
        df = pd.DataFrame({
            'time': pd.date_range('2024-01-01', periods=100),
            'open': np.random.rand(100),
            'high': np.random.rand(100),
            'low': np.random.rand(100),
            'close': np.random.rand(100),
        })
        
        logger.info(f"✓ Created test DataFrame with {len(df)} rows")
        logger.info(f"✓ Columns: {', '.join(df.columns)}")
        
        # Test timezone conversion
        import pytz
        tz = pytz.timezone("Africa/Nairobi")
        logger.info(f"✓ Timezone loaded: {tz}")
        
        logger.info("\n✓ Data processing test passed!")
        return True
    
    except Exception as e:
        logger.error(f"\n✗ Data processing error: {e}")
        return False


def test_scanner_logic():
    """Test scanner logic without MT5"""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: Scanner Logic")
    logger.info("="*70)
    
    try:
        from src.forex_scanner.utils import (
            get_nairobi_time, get_4h_candle_info, format_price, format_pips
        )
        
        logger.info("Testing utility functions...")
        
        now = get_nairobi_time()
        logger.info(f"✓ Current Nairobi time: {now.strftime('%H:%M:%S')}")
        
        candle_info = get_4h_candle_info()
        logger.info(f"✓ 8am Candle Progress: {candle_info['percentage_complete']:.0f}%")
        logger.info(f"✓ Minutes Elapsed: {candle_info['minutes_elapsed']}/240")
        
        # Test formatting
        price = 1.09456
        pips = 35.5
        logger.info(f"✓ Format Price: {format_price(price)}")
        logger.info(f"✓ Format Pips: {format_pips(pips)}")
        
        logger.info("\n✓ Scanner logic test passed!")
        return True
    
    except Exception as e:
        logger.error(f"\n✗ Scanner logic error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def print_final_report(results):
    """Print final test report"""
    logger.info("\n" + "="*70)
    logger.info("FINAL TEST REPORT")
    logger.info("="*70 + "\n")
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "="*70)
    
    if all_passed:
        logger.info("\n✅ ALL TESTS PASSED! Scanner is ready to run.\n")
        logger.info("Next steps:")
        logger.info("  • Run live scanner: python main.py")
        logger.info("  • Open dashboard: streamlit run dashboard/app.py")
        logger.info("  • Run backtest: python backtest/backtest.py")
    else:
        logger.warning("\n❌ SOME TESTS FAILED. Review the errors above.\n")
        logger.info("Common fixes:")
        logger.info("  • MetaTrader5 not found → Install: pip install MetaTrader5")
        logger.info("  • Connection failed → Launch MT5 and login to your account")
        logger.info("  • Configuration error → Copy .env.example to .env and fill in details")
    
    return 0 if all_passed else 1


def main():
    """Run all tests"""
    logger.info("\n" + "🧪 FOREX SCANNER - DIAGNOSTIC TEST SUITE\n")
    
    results = {
        "Configuration Loading": test_configuration(),
        "Data Processing": test_data_processing(),
        "Scanner Logic": test_scanner_logic(),
        "MetaTrader5 Connection": test_mt5_connection(),
        "Alert Configuration": test_alerts(),
    }
    
    return print_final_report(results)


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
