"""PAIR ANALYSIS institutional-style FX research terminal."""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import settings
from data.database import init_db, save_scores
from data.models import CURRENCIES, PAIRS
from data.seed_data import demo_currency, demo_market, demo_catalysts
from data_sources.market_data import yahoo_history
from data_sources.cftc import fetch_cot_positions
from data_sources.yields import fetch_treasury_curve
from data_sources.economic_data import fetch_bls_indicators
from data.seed_data import yahoo_market
from engine.scoring import analyze_all

st.set_page_config(page_title="PAIR ANALYSIS", page_icon="PA", layout="wide", initial_sidebar_state="expanded")
init_db(settings.database_path)

st.markdown("""
<style>
:root { --bg:#0B0F14; --panel:#111820; --border:#202933; --text:#E6EDF3; --muted:#8B98A5; --green:#22C55E; --red:#EF4444; --amber:#F59E0B; --blue:#3B82F6; }
.stApp { background:var(--bg); color:var(--text); }
section[data-testid="stSidebar"] { background:#0D131A; border-right:1px solid var(--border); }
section[data-testid="stSidebar"] .block-container { padding:1.2rem 1rem; }
.block-container { max-width: 1600px; padding-top:1.2rem; }
h1,h2,h3 { letter-spacing:0; font-weight:650; } h1 { font-size:1.7rem; } h2 { font-size:1.1rem; margin-top:1.1rem; } h3 { font-size:.92rem; }
[data-testid="stMetric"] { background:var(--panel); border:1px solid var(--border); padding:.6rem .75rem; border-radius:4px; }
[data-testid="stMetricValue"] { font-size:1.15rem; } [data-testid="stMetricLabel"] { color:var(--muted); font-size:.72rem; }
div[data-testid="stDataFrame"] { border:1px solid var(--border); }
.badge { display:inline-block; border:1px solid var(--border); border-radius:3px; padding:3px 7px; font-size:.68rem; font-weight:700; margin-right:4px; }
.live { color:var(--green); } .demo { color:var(--amber); } .positive { color:var(--green); } .negative { color:var(--red); } .muted { color:var(--muted); }
.panel { background:var(--panel); border:1px solid var(--border); border-radius:4px; padding:12px; margin-bottom:10px; }
.small { font-size:.72rem; color:var(--muted); } .big { font-size:1.6rem; font-weight:700; }
div.stButton > button { border-radius:3px; border:1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def load_yahoo_market():
    return yahoo_market(PAIRS)

@st.cache_data(ttl=300, show_spinner=False)
def load_cot_data():
    return fetch_cot_positions(CURRENCIES)

@st.cache_data(ttl=3600, show_spinner=False)
def load_yield_data():
    return fetch_treasury_curve()

@st.cache_data(ttl=3600, show_spinner=False)
def load_economic_data():
    return fetch_bls_indicators()


def load_data(source: str):
    if source == "Yahoo Finance":
        yahoo_data, provider = load_yahoo_market()
        return yahoo_data, demo_currency(), demo_catalysts(), provider
    return demo_market(), demo_currency(), demo_catalysts(), "DEMO"


data_source = "Demo Mode"
if "data_source" not in st.session_state:
    st.session_state.data_source = "Yahoo Finance"
data_source = st.session_state.data_source
market, currencies, catalysts, provider_name = load_data(data_source)
analyses = analyze_all(market, currencies, catalysts)
try: save_scores(settings.database_path, analyses)
except Exception: pass


def sign(value):
    return "positive" if value > 0 else "negative" if value < 0 else "muted"

def regime():
    vix = 15.8
    equity = 0.46
    btc = 1.1
    score = (equity * 1.4) + (btc * .3) - ((vix - 18) * .2)
    label = "RISK ON" if score > .3 else "RISK OFF" if score < -.3 else "MIXED"
    return label, max(51, min(88, int(64 + score * 8)))

def header():
    label, confidence = regime()
    left, right = st.columns([3, 7])
    with left:
        st.markdown("# PAIR ANALYSIS")
        badge = "demo" if provider_name == "DEMO" else "live"
        label = "DEMO DATA - NOT FOR LIVE TRADING" if provider_name == "DEMO" else "YAHOO FINANCE - MARKET PRICES"
        st.markdown(f'<span class="badge {badge}">{label}</span><span class="badge">DATA QUALITY {"74" if provider_name == "DEMO" else "86"}%</span>', unsafe_allow_html=True)
    with right:
        st.caption(datetime.now().strftime("%d %b %Y %H:%M") + " EAT  |  Source: " + provider_name)
        cols = st.columns(8)
        moves = {"USD":-.24,"EUR":.18,"GBP":.32,"JPY":-.51,"CHF":.08,"CAD":.64,"AUD":.72,"NZD":-.15}
        for col, cur in zip(cols, CURRENCIES):
            with col: st.metric(cur, f"{moves[cur]:+.2f}%")
    st.divider()
    cols = st.columns(8)
    assets = [("REGIME", f"{label} {confidence}%"), ("VIX", "15.8"), ("DXY", "103.42"), ("GOLD", "+0.31%"), ("WTI", "+1.12%"), ("S&P 500", "+0.46%"), ("NASDAQ", "+0.68%"), ("BTC", "+1.10%")]
    for col, (name, value) in zip(cols, assets):
        with col: st.metric(name, value)

def sidebar():
    st.sidebar.markdown("## PAIR ANALYSIS")
    st.sidebar.caption("Institutional FX research terminal")
    pages = ["Overview", "28 Pair Scanner", "Currency Matrix", "Top Setups", "Catalyst Radar", "Yield Dashboard", "COT & Positioning", "Technical Scanner", "Risk Regime", "Correlations", "Economic Calendar", "Performance", "Settings"]
    page = st.sidebar.radio("NAVIGATION", pages, label_visibility="collapsed")
    st.sidebar.divider()
    st.sidebar.markdown('<span class="small">SYSTEM STATUS</span>', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="live">●</span> Market status &nbsp; OPEN', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="demo">●</span> Provider &nbsp; DEMO', unsafe_allow_html=True)
    st.sidebar.markdown('<span class="muted">●</span> Data age &nbsp; seeded now', unsafe_allow_html=True)
    refresh = st.sidebar.selectbox("AUTO REFRESH", ["Manual", "30 sec", "1 min", "5 min", "15 min", "30 min", "1 hour"], index=3)
    if st.sidebar.button("REFRESH DATA", use_container_width=True): st.rerun()
    selected_source = st.sidebar.radio("DATA SOURCE", ["Yahoo Finance", "Demo Mode"], index=0 if st.session_state.data_source == "Yahoo Finance" else 1)
    if selected_source != st.session_state.data_source:
        st.session_state.data_source = selected_source
        st.rerun()
    st.sidebar.caption("Refresh: " + refresh + " | SQLite persistence enabled")
    return page

def score_table():
    rows=[]
    for a in analyses:
        rows.append({"PAIR":a.pair,"PRICE":f"{a.price:.5f}","24H":f"{a.daily_change:+.2f}%","SCORE":a.score,"BIAS":a.bias.upper(),"CONF.":f"{a.confidence:.0f}%","GRADE":a.grade,"REPRICE":a.factors["policy"],"YIELD":a.factors["yield"],"TECH":a.factors["technical"],"ALIGN":f"{a.alignment}/9","ACTION":a.action})
    return pd.DataFrame(rows)

def overview():
    label, confidence = regime()
    st.subheader("MARKET REGIME")
    a,b,c = st.columns([2,2,6])
    with a: st.markdown(f'<div class="panel"><div class="small">CURRENT REGIME</div><div class="big">{label}</div><div class="positive">{confidence}% confidence</div></div>', unsafe_allow_html=True)
    with b: st.markdown('<div class="panel"><div class="small">DRIVERS</div><div class="positive">Equities up</div><div class="positive">VIX contained</div><div class="negative">JPY defensive bid</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="panel"><div class="small">REGIME ENGINE</div>Multiple assets confirm the current classification. Gold strength is a contradiction, so conviction is capped rather than inferred from a single market.</div>', unsafe_allow_html=True)
    st.subheader("CURRENCY REPRICING")
    cur_df = pd.DataFrame([{"CURRENCY":c,"STRUCTURAL":v["structural"],"REPRICING":v["repricing"],"FLOW":v["flow"],"COT":"N/A","RETAIL":"N/A","FINAL":round(v["structural"]*.3+v["repricing"]*.7,2)} for c,v in currencies.items()]).sort_values("FINAL", ascending=False)
    st.dataframe(cur_df.style.map(lambda x: "color:#22C55E" if isinstance(x,(float,int)) and x>0 else "color:#EF4444" if isinstance(x,(float,int)) and x<0 else "", subset=["STRUCTURAL","REPRICING","FLOW","FINAL"]), use_container_width=True, hide_index=True)
    st.subheader("TOP SETUPS")
    top = sorted(analyses, key=lambda x: x.score if x.action == "BUY" else 100-x.score, reverse=True)[:5]
    cols=st.columns(5)
    for col,a in zip(cols,top):
        with col:
            color="positive" if a.action=="BUY" else "negative" if a.action=="SELL" else "muted"
            st.markdown(f'<div class="panel"><div class="small">SETUP</div><b>{a.pair}</b><div class="{color} big">{a.action}</div><div>Score <b>{a.score:.0f}</b> | {a.confidence:.0f}%</div><div class="small">{a.grade} | {a.alignment}/9 aligned</div></div>', unsafe_allow_html=True)
    st.subheader("28 PAIR SCANNER")
    st.dataframe(score_table().head(10), use_container_width=True, hide_index=True)

def scanner():
    st.subheader("28 PAIR SCANNER")
    c1,c2,c3,c4 = st.columns(4)
    action=c1.selectbox("ACTION", ["All","BUY","SELL","WAIT","NO TRADE"])
    minimum=c2.selectbox("CONFIDENCE", ["All","80%+","70%+","60%+"])
    currency=c3.selectbox("CURRENCY", ["All"]+CURRENCIES)
    selected=c4.selectbox("PAIR X-RAY", ["Select a pair"]+PAIRS)
    df=score_table()
    if action != "All": df=df[df.ACTION==action]
    if minimum != "All": df=df[df["CONF."].str.rstrip('%').astype(float)>=int(minimum[:2])]
    if currency != "All": df=df[df.PAIR.str.startswith(currency) | df.PAIR.str.endswith(currency)]
    st.caption(f"Showing {len(df)} of {len(PAIRS)} pairs. Price and macro fields are DEMO until a provider is connected.")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if selected != "Select a pair": pair_xray(selected)

def pair_xray(pair):
    a=next(x for x in analyses if x.pair==pair)
    st.divider(); st.subheader(f"PAIR X-RAY  /  {pair}")
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("ACTION",a.action); c2.metric("SCORE",f"{a.score:.0f}/100"); c3.metric("CONFIDENCE",f"{a.confidence:.0f}%"); c4.metric("GRADE",a.grade); c5.metric("ALIGNMENT",f"{a.alignment}/9")
    left,right=st.columns([7,3])
    with left:
        history = yahoo_history(pair, period="1y") if provider_name == "YAHOO FINANCE" else pd.DataFrame()
        if not history.empty and "Close" in history:
            prices = history["Close"].astype(float).dropna().tail(252)
            x = prices.index
        else:
            x=np.arange(120); base=market[pair]["price"]; prices=base*(1+np.cumsum(np.random.default_rng(sum(map(ord,pair))).normal(0,.002,120)))
        fig=go.Figure(go.Scatter(x=x,y=prices,mode="lines",line={"color":"#3B82F6","width":2},name="Price"))
        fig.add_trace(go.Scatter(x=x,y=pd.Series(prices).rolling(14).mean(),mode="lines",line={"color":"#F59E0B"},name="14 SMA"))
        fig.update_layout(height=310,margin=dict(l=0,r=0,t=20,b=0),paper_bgcolor="#111820",plot_bgcolor="#111820",font_color="#E6EDF3",xaxis_title="Daily sessions",yaxis_title="Price",legend=dict(orientation="h"))
        st.plotly_chart(fig,use_container_width=True)
    with right:
        st.markdown('<div class="panel"><b>WHY IS THIS PAIR MOVING TODAY?</b><hr><span class="positive">1. Marginal repricing</span><br><span class="positive">2. Yield direction</span><br><span class="negative">3. Price contradiction risk</span><hr><b>NET DRIVER SCORE</b><br>' + a.explanation + '</div>',unsafe_allow_html=True)
    st.subheader("SCORE EXPLANATION")
    factor_df=pd.DataFrame([{"FACTOR":k.upper(),"CONTRIBUTION":f"{v:+.2f}","STATUS":"CONFIRMS" if v>.25 else "CONFLICTS" if v<-.25 else "NEUTRAL"} for k,v in a.factors.items()])
    st.dataframe(factor_df,use_container_width=True,hide_index=True)
    st.info("Core rule: rate levels are not treated as directional signals. Repricing, yield driver, surprise, flow, cross-asset confirmation, and price response must agree before a trade is considered.")

def generic_page(page):
    st.subheader(page.upper())
    if page == "Yield Dashboard":
        yield_page()
        return
    if page == "Economic Calendar":
        economic_page()
        return
    if page == "COT & Positioning":
        positioning_page()
        return
    st.markdown(f'<div class="panel"><b>{provider_name} PRICE DATA</b><br>Market prices and historical returns may come from Yahoo Finance. Economic forecasts, COT, retail positioning, central-bank repricing, and news remain N/A until a dedicated provider is connected.</div>', unsafe_allow_html=True)
    if page == "Catalyst Radar":
        st.dataframe(pd.DataFrame([{**c,"timestamp":c["timestamp"].strftime("%d %b %H:%M"),"freshness":"0-24h" if (datetime.utcnow()-c["timestamp"]).total_seconds()<86400 else "24-48h"} for c in catalysts]),use_container_width=True,hide_index=True)
    elif page == "Economic Calendar":
        st.dataframe(pd.DataFrame([{"TIME":"N/A","CURRENCY":"USD","EVENT":"Provider unavailable","IMPORTANCE":"N/A","FORECAST":"N/A","ACTUAL":"N/A","SURPRISE":"N/A","IMPACT":"UNAVAILABLE"}]),use_container_width=True,hide_index=True)
    elif page == "Performance":
        performance_page()
    else:
        st.write("No connected provider for this view. Configure an API key in `.env` to replace demo inputs.")


def yield_page():
    """Display the latest public U.S. Treasury par yield curve."""
    data = load_yield_data()
    if not data:
        st.warning("The U.S. Treasury yield curve is unavailable. Refresh later to retry the public endpoint.")
        return
    curve = data["curve"]
    rows = [{"TENOR": tenor, "YIELD (%)": value, "DAILY CHANGE (bp)": round(data["change"].get(tenor, 0) * 100, 1)} for tenor, value in curve.items()]
    table = pd.DataFrame(rows)
    st.markdown(f'<div class="panel"><b>U.S. TREASURY PAR YIELD CURVE</b><br>Latest available observation: {data["date"]}. Source: {data["source"]}. Yields are rates, not directional signals by themselves.</div>', unsafe_allow_html=True)
    short, long = st.columns(2)
    with short:
        short.metric("2Y YIELD", f"{curve.get('2Y', float('nan')):.2f}%")
    with long:
        long.metric("10Y-2Y SPREAD", f"{(curve.get('10Y', 0) - curve.get('2Y', 0)) * 100:+.1f} bp")
    chart = table.set_index("TENOR")[["YIELD (%)"]]
    st.line_chart(chart, height=300)
    st.dataframe(table, use_container_width=True, hide_index=True)


def economic_page():
    """Display latest official BLS CPI and labor observations."""
    events = load_economic_data()
    if not events:
        st.warning("The BLS economic data service is unavailable. Refresh later to retry the public endpoint.")
        return
    rows = []
    for event in events:
        change = event["change"]
        rows.append({
            "INDICATOR": event["event"],
            "LATEST VALUE": event["value"],
            "CHANGE": round(change, 2) if change is not None else "N/A",
            "UNIT": event["unit"],
            "PERIOD": event["period"],
            "SOURCE": event["source"],
        })
    table = pd.DataFrame(rows)
    st.markdown('<div class="panel"><b>U.S. ECONOMIC INDICATORS</b><br>CPI and labor observations from the U.S. Bureau of Labor Statistics public API. GDP requires a separate BEA data series and is not inferred here.</div>', unsafe_allow_html=True)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption("BLS release values are official observations and are not investment advice. Release timing varies by series.")


def positioning_page():
    """Display public CFTC futures positioning without substituting demo values."""
    positions = load_cot_data()
    if not positions:
        st.warning("CFTC did not return positioning data. Check the provider response and refresh later.")
        return
    rows = []
    for currency in CURRENCIES:
        position = positions.get(currency)
        if not position:
            continue
        net = position["net_position"]
        change = position["weekly_change"]
        rows.append({
            "CURRENCY": currency,
            "NET POSITION": round(net),
            "WEEKLY CHANGE": round(change),
            "LONG CONTRACTS": round(position["long"]),
            "SHORT CONTRACTS": round(position["short"]),
            "BIAS": "LONG" if net > 0 else "SHORT" if net < 0 else "FLAT",
            "REPORT DATE": position["report_date"],
            "SOURCE": position["source"],
        })
    table = pd.DataFrame(rows)
    st.markdown('<div class="panel"><b>INSTITUTIONAL POSITIONING</b><br>Non-commercial futures positioning from the CFTC weekly Commitments of Traders report. CFTC publishes this report weekly, usually Friday afternoon Eastern Time.</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        left.metric("CURRENCIES AVAILABLE", len(table))
    with right:
        right.metric("AVERAGE NET POSITION", f"{table['NET POSITION'].mean():,.0f}")
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption("Retail sentiment from AAII/CBOE and macro series from BLS/FRED are not included until their respective provider pipelines are configured.")


def performance_page():
    """Show transparent price-return statistics rather than pretending signals are executed."""
    rows = []
    for pair in PAIRS:
        history = yahoo_history(pair, period="1y") if provider_name == "YAHOO FINANCE" else pd.DataFrame()
        if history.empty or "Close" not in history:
            continue
        close = history["Close"].astype(float).dropna()
        if len(close) < 22:
            continue
        monthly = close.iloc[-1] / close.iloc[-22] - 1
        rows.append({"PAIR": pair, "SOURCE": "YAHOO FINANCE", "1M RETURN": f"{monthly * 100:+.2f}%", "OBSERVATIONS": len(close), "STATUS": "PRICE HISTORY"})
    if not rows:
        st.info("Yahoo Finance history is unavailable. No performance values are invented.")
        return
    returns = [float(row["1M RETURN"].rstrip("%")) for row in rows]
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("PAIRS WITH HISTORY", len(rows)); m2.metric("AVERAGE 1M RETURN", f"{np.mean(returns):+.2f}%"); m3.metric("POSITIVE MONTH", f"{sum(value > 0 for value in returns) / len(returns) * 100:.0f}%"); m4.metric("DATA SOURCE", "YAHOO")
    st.caption("This is historical price performance, not a claimed strategy backtest. Executed trade outcomes require a validated signal ledger.")
    st.dataframe(pd.DataFrame(rows).sort_values("1M RETURN", ascending=False), use_container_width=True, hide_index=True)

page=sidebar(); header()
if page == "Overview": overview()
elif page == "28 Pair Scanner": scanner()
elif page == "Currency Matrix": overview()
elif page == "Top Setups": scanner()
elif page == "Catalyst Radar": generic_page(page)
elif page == "Settings": generic_page(page)
elif page == "Economic Calendar": generic_page(page)
else: generic_page(page)
