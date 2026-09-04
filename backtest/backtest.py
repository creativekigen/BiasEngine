"""
Standalone Backtest Script
Test the 4H setup across historical data
"""

import argparse
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector
from src.forex_scanner.data_processor import DataProcessor
from src.forex_scanner.utils import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/backtest.log", level="INFO")


def format_results(results):
    """Pretty print backtest results"""
    print("\n" + "="*100)
    print("BACKTEST RESULTS SUMMARY")
    print("="*100 + "\n")
    
    summary_data = []
    total_setups = 0
    total_breakouts = 0
    total_profitable = 0
    total_losing = 0
    
    for pair in sorted(results.keys()):
        data = results[pair]
        
        if "error" in data:
            print(f"✗ {pair}: ERROR - {data['error']}")
            continue
        
        total_setups += data['total_setups']
        total_breakouts += data['total_breakouts']
        total_profitable += data['profitable_trades']
        total_losing += data['losing_trades']
        
        summary_data.append({
            "Pair": pair,
            "Period": f"{data['start_date']} to {data['end_date']}",
            "Setups": data['total_setups'],
            "Breakouts": data['total_breakouts'],
            "Profitable": data['profitable_trades'],
            "Losing": data['losing_trades'],
            "Breakeven": data['breakeven_trades'],
            "Win Rate": f"{data['win_rate_percent']:.1f}%",
            "Setup→Breakout": f"{data['setup_to_breakout_rate_percent']:.1f}%",
        })
    
    # Display summary
    for item in summary_data:
        print(f"{item['Pair']:12} | Setups: {item['Setups']:3} | Breakouts: {item['Breakouts']:3} | "
              f"Profitable: {item['Profitable']:3} | Losing: {item['Losing']:3} | "
              f"Win Rate: {item['Win Rate']:6} | Setup→Breakout: {item['Setup→Breakout']:6}")
    
    print("\n" + "-"*100)
    
    # Calculate overall statistics
    if total_breakouts > 0:
        overall_win_rate = (total_profitable / total_breakouts) * 100
    else:
        overall_win_rate = 0
    
    if total_setups > 0:
        setup_to_breakout = (total_breakouts / total_setups) * 100
    else:
        setup_to_breakout = 0
    
    print(f"\n{'OVERALL STATISTICS':^100}")
    print("-"*100)
    print(f"Total Setups Found:        {total_setups}")
    print(f"Total Breakouts Detected:  {total_breakouts}")
    print(f"Profitable Trades:         {total_profitable}")
    print(f"Losing Trades:             {total_losing}")
    print(f"Breakeven Trades:          {results[list(results.keys())[0]].get('breakeven_trades', 0)}")
    print(f"\nOverall Win Rate:          {overall_win_rate:.1f}%")
    print(f"Setup→Breakout Conversion: {setup_to_breakout:.1f}%")
    print("\n" + "="*100 + "\n")


def run_single_pair_backtest(pair: str, start_date: str, end_date: str):
    """Run backtest for a single pair"""
    try:
        # Connect to MT5
        logger.info("Connecting to MetaTrader5...")
        mt5 = MT5Connector()
        
        if not mt5.connect():
            logger.error("Failed to connect to MT5")
            return
        
        logger.info("✓ Connected to MT5")
        
        # Run backtest
        processor = DataProcessor(mt5)
        logger.info(f"\nRunning backtest for {pair}...")
        logger.info(f"Period: {start_date} to {end_date}")
        
        result = processor.backtest_setup(pair, start_date, end_date)
        
        # Format and display results
        if "error" not in result:
            print("\n" + "="*80)
            print(f"BACKTEST RESULTS - {pair}")
            print("="*80)
            print(f"Period:                    {start_date} to {end_date}")
            print(f"Total Setups Found:        {result['total_setups']}")
            print(f"Total Breakouts:           {result['total_breakouts']}")
            print(f"Profitable Trades:         {result['profitable_trades']}")
            print(f"Losing Trades:             {result['losing_trades']}")
            print(f"Breakeven Trades:          {result['breakeven_trades']}")
            print(f"\nWin Rate:                  {result['win_rate_percent']:.1f}%")
            print(f"Setup→Breakout Rate:       {result['setup_to_breakout_rate_percent']:.1f}%")
            print("="*80 + "\n")
            
            # Display detailed trades
            if result['details']:
                print("Detailed Trade Results:")
                print("-"*80)
                for trade in result['details']:
                    status = "✓ WIN" if trade['profitable'] else "✗ LOSS"
                    print(f"{status} | {trade['date']} | Low: {trade['low_price']:.5f} | "
                          f"Breakout: {trade['breakout_price']:.5f} | "
                          f"Pips: {trade['pips']:+.1f}")
                print("-"*80 + "\n")
        else:
            logger.error(f"Backtest error: {result['error']}")
        
        # Disconnect
        mt5.disconnect()
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())


def run_all_pairs_backtest(start_date: str, end_date: str):
    """Run backtest for all configured pairs"""
    try:
        # Connect to MT5
        logger.info("Connecting to MetaTrader5...")
        mt5 = MT5Connector()
        
        if not mt5.connect():
            logger.error("Failed to connect to MT5")
            return
        
        logger.info("✓ Connected to MT5")
        
        # Run backtest
        processor = DataProcessor(mt5)
        logger.info(f"\nRunning backtest for {len(config.FOREX_PAIRS)} pairs...")
        logger.info(f"Period: {start_date} to {end_date}\n")
        
        results = processor.backtest_all_pairs(start_date, end_date)
        
        # Display results
        format_results(results)
        
        # Save results
        logger.info("Saving results...")
        processor.save_backtest_results(results)
        processor.export_signal_details(results)
        logger.info("✓ Results saved to CSV files")
        
        # Disconnect
        mt5.disconnect()
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Forex Scanner Backtest Tool"
    )
    
    parser.add_argument(
        "--pair",
        help="Specific pair to backtest (default: all pairs)",
        default=None
    )
    
    parser.add_argument(
        "--start",
        help="Start date (YYYY-MM-DD)",
        default=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    )
    
    parser.add_argument(
        "--end",
        help="End date (YYYY-MM-DD)",
        default=datetime.now().strftime("%Y-%m-%d")
    )
    
    parser.add_argument(
        "--verbose",
        help="Enable verbose logging",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_file="logs/backtest.log", level=log_level)
    
    logger.info("="*80)
    logger.info("Forex Scanner - Backtest Tool")
    logger.info("="*80)
    
    # Validate dates
    try:
        start_dt = datetime.strptime(args.start, "%Y-%m-%d")
        end_dt = datetime.strptime(args.end, "%Y-%m-%d")
        
        if start_dt >= end_dt:
            logger.error("Start date must be before end date")
            return 1
        
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return 1
    
    # Run backtest
    if args.pair:
        if args.pair not in config.FOREX_PAIRS:
            logger.warning(f"Pair {args.pair} not in configured pairs")
        run_single_pair_backtest(args.pair, args.start, args.end)
    else:
        run_all_pairs_backtest(args.start, args.end)
    
    return 0


if __name__ == "__main__":
    exit(main())
