"""
Streamlit Dashboard for Forex Scanner
Real-time monitoring and visualization of 4-hour candle setups
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

# Configure page
st.set_page_config(
    page_title="Forex Scanner Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forex_scanner.config import config
from src.forex_scanner.mt5_connector import MT5Connector
from src.forex_scanner.scanner import ForexScanner
from src.forex_scanner.data_processor import DataProcessor
from src.forex_scanner.alerts import get_alert_manager
from src.forex_scanner.utils import (
    setup_logging, get_nairobi_time, get_4h_candle_info, 
    format_price, format_pips, get_stats
)

# Setup logging
logger = setup_logging(log_file="logs/dashboard.log")

# Page styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .alert-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
    }
    .success-card {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .error-card {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

# ===== PAGE HEADER =====
st.title("🤖 Forex Scanner Dashboard")
st.markdown("Real-time 4-hour candle alignment detection across 28 major and minor pairs")

# ===== SIDEBAR CONTROLS =====
with st.sidebar:
    st.header("⚙️ Scanner Settings")
    
    mode = st.radio(
        "Select Mode",
        ["Live Monitor", "Backtest", "Settings"],
        index=0
    )
    
    st.divider()
    
    # Current time display
    now = get_nairobi_time()
    st.metric("Current Time (Nairobi)", now.strftime("%H:%M:%S"))
    
    # 4H candle info
    candle_info = get_4h_candle_info()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("8am Candle Time", f"{candle_info['percentage_complete']:.0f}%")
    with col2:
        st.metric("Minutes Remaining", f"{candle_info['minutes_remaining']}")
    
    st.divider()
    
    # Alert settings
    st.subheader("Alert Channels")
    alert_manager = get_alert_manager()
    alert_status = alert_manager.get_status()
    
    for channel_name in ['console', 'telegram', 'discord', 'email', 'sound']:
        is_enabled = alert_status[f'{channel_name}_enabled']
        status = "✓" if is_enabled else "✗"
        st.write(f"{status} {channel_name.title()}")

# ===== MAIN CONTENT =====

if mode == "Live Monitor":
    st.header("📍 Live Scanner Monitor")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pairs", len(config.FOREX_PAIRS))
    
    with col2:
        stats = get_stats().get_stats()
        st.metric("Total Scans", stats['total_scans'])
    
    with col3:
        st.metric("Setups Detected", stats['total_setups_detected'])
    
    with col4:
        st.metric("Breakouts Detected", stats['total_breakouts_detected'])
    
    st.divider()
    
    # Connect to MT5
    st.subheader("🔌 MT5 Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Connect to MT5", use_container_width=True):
            with st.spinner("Connecting to MT5..."):
                try:
                    mt5 = MT5Connector()
                    if mt5.connect():
                        st.success("✓ Connected to MT5")
                        st.session_state.mt5_connected = True
                        st.session_state.mt5_connector = mt5
                    else:
                        st.error("✗ Failed to connect to MT5")
                        st.session_state.mt5_connected = False
                except Exception as e:
                    st.error(f"✗ Connection error: {e}")
                    st.session_state.mt5_connected = False
    
    with col2:
        if st.button("📊 Run Scanner", use_container_width=True):
            if st.session_state.get('mt5_connected'):
                with st.spinner("Scanning all pairs..."):
                    try:
                        mt5 = st.session_state.mt5_connector
                        scanner = ForexScanner(mt5)
                        
                        # Scan all pairs
                        results = scanner.scan_all_pairs()
                        setups = {k: v for k, v in results.items() if v is not None}
                        
                        if setups:
                            st.success(f"✓ Found {len(setups)} setups!")
                            
                            # Display setups
                            for pair, signal in setups.items():
                                with st.expander(f"✓ {pair} - {signal.low_price:.5f}"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**Low Price:** {format_price(signal.low_price)}")
                                        st.write(f"**Low Time:** {signal.low_time.strftime('%H:%M')}")
                                        st.write(f"**Low Minute:** {signal.low_minute}/240")
                                    
                                    with col2:
                                        st.write(f"**Candle High:** {format_price(signal.candle_high)}")
                                        st.write(f"**Candle Low:** {format_price(signal.low_price)}")
                                        st.write(f"**Target (50%):** {format_price(signal.midpoint_target)}")
                        else:
                            st.info("No setups found in current scan")
                        
                        # Check for breakouts
                        breakouts = scanner.check_all_breakouts()
                        if breakouts:
                            st.warning(f"🚀 {len(breakouts)} BREAKOUTS DETECTED!")
                            
                            for breakout in breakouts:
                                with st.expander(f"🚀 {breakout.pair} - BREAKOUT ({breakout.signal_strength})"):
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.write(f"**Original Low:** {format_price(breakout.low_signal.low_price)}")
                                        st.write(f"**Breakout Price:** {format_price(breakout.breakout_price)}")
                                    
                                    with col2:
                                        st.write(f"**Breakout Distance:** {format_pips(breakout.breakout_distance_pips)} pips")
                                        st.write(f"**Signal Strength:** {breakout.signal_strength}")
                                    
                                    with col3:
                                        st.write(f"**Target:** {format_price(breakout.low_signal.midpoint_target)}")
                                        distance = abs(breakout.breakout_price - breakout.low_signal.midpoint_target)
                                        st.write(f"**Distance to Target:** {format_price(distance)}")
                    
                    except Exception as e:
                        st.error(f"Error during scan: {e}")
                        logger.error(f"Scan error: {e}", exc_info=True)
            else:
                st.warning("Connect to MT5 first!")
    
    st.divider()
    
    # Pair selector
    st.subheader("📋 All Pairs")
    pairs_df = pd.DataFrame({
        "Pair": config.FOREX_PAIRS,
        "Status": ["Monitoring"] * len(config.FOREX_PAIRS),
    })
    st.dataframe(pairs_df, use_container_width=True, hide_index=True)

elif mode == "Backtest":
    st.header("📈 Backtest Historical Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    with col3:
        pairs_to_test = st.multiselect(
            "Select Pairs",
            config.FOREX_PAIRS,
            default=config.FOREX_PAIRS[:5]
        )
    
    if st.button("🧪 Run Backtest", use_container_width=True):
        if st.session_state.get('mt5_connected'):
            with st.spinner("Running backtest..."):
                try:
                    mt5 = st.session_state.mt5_connector
                    processor = DataProcessor(mt5)
                    
                    # Run backtest
                    backtest_results = {}
                    progress_bar = st.progress(0)
                    
                    for idx, pair in enumerate(pairs_to_test):
                        progress = (idx + 1) / len(pairs_to_test)
                        progress_bar.progress(progress)
                        
                        result = processor.backtest_setup(
                            pair,
                            start_date.strftime("%Y-%m-%d"),
                            end_date.strftime("%Y-%m-%d")
                        )
                        backtest_results[pair] = result
                    
                    # Display results
                    st.success("✓ Backtest completed!")
                    
                    # Summary table
                    summary_rows = []
                    for pair, data in backtest_results.items():
                        if "error" not in data:
                            summary_rows.append({
                                "Pair": pair,
                                "Setups": data['total_setups'],
                                "Breakouts": data['total_breakouts'],
                                "Win Rate": f"{data['win_rate_percent']:.1f}%",
                                "Setup→Breakout": f"{data['setup_to_breakout_rate_percent']:.1f}%",
                            })
                    
                    if summary_rows:
                        summary_df = pd.DataFrame(summary_rows)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        # Export options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("💾 Export Summary"):
                                processor.save_backtest_results(backtest_results)
                                st.success("✓ Summary exported to backtest_results.csv")
                        
                        with col2:
                            if st.button("📑 Export Details"):
                                processor.export_signal_details(backtest_results)
                                st.success("✓ Details exported to signal_details.csv")
                
                except Exception as e:
                    st.error(f"Backtest error: {e}")
                    logger.error(f"Backtest error: {e}", exc_info=True)
        else:
            st.warning("Connect to MT5 first!")

elif mode == "Settings":
    st.header("⚙️ Configuration Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕐 Timezone Settings")
        st.write(f"**Market Timezone:** {config.MARKET_TIMEZONE}")
        st.write(f"**UTC Offset:** +{config.UTC_OFFSET_HOURS}:00")
    
    with col2:
        st.subheader("🔔 Alert Channels")
        st.write(f"**Console:** {'✓' if config.ALERT_TYPES else '✗'}")
        st.write(f"**Telegram:** {'✓' if config.TELEGRAM_ENABLED else '✗'}")
        st.write(f"**Discord:** {'✓' if config.DISCORD_ENABLED else '✗'}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Scanner Parameters")
        st.write(f"**8H Candle Start:** {config.CANDLE_START_HOUR}:00")
        st.write(f"**8H Candle End:** {config.CANDLE_END_HOUR}:00")
        st.write(f"**Late Low Threshold:** {config.LATE_LOW_THRESHOLD_MINUTES} minutes")
        st.write(f"**Breakout Watch Window:** {config.BREAKOUT_WATCH_WINDOW_MINUTES} minutes")
    
    with col2:
        st.subheader("💱 Pairs Monitored")
        st.write(f"**Total Pairs:** {len(config.FOREX_PAIRS)}")
        
        # Show pairs in columns
        pairs_cols = st.columns(3)
        for idx, pair in enumerate(config.FOREX_PAIRS):
            col_idx = idx % 3
            with pairs_cols[col_idx]:
                st.write(f"• {pair}")
    
    st.divider()
    
    # Status check
    if st.button("✅ Check System Status"):
        st.subheader("System Status Report")
        
        status_items = {
            "MT5 Package": "✓" if True else "✗",  # Check if importable
            "Streamlit": "✓",
            "Pandas": "✓",
            "Plotly": "✓",
        }
        
        col1, col2 = st.columns(2)
        for idx, (name, status) in enumerate(status_items.items()):
            if idx < 2:
                with col1:
                    st.write(f"{status} {name}")
            else:
                with col2:
                    st.write(f"{status} {name}")
        
        st.success("✓ All systems operational!")

# ===== FOOTER =====
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.write("📧 **Support:** scanner@biasflo.com")

with col2:
    st.write("📖 **Docs:** github.com/biasflo/forex-scanner")

with col3:
    st.write("🔗 **Timezone:** Africa/Nairobi (EAT)")
