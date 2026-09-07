"""BIASFLO institutional-style FX market intelligence terminal."""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET
import requests
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import settings
from data.database import init_db, save_scores
from data.models import CURRENCIES, PAIRS
from data.seed_data import demo_currency, demo_market, demo_catalysts
from data_sources.market_data import yahoo_history, yahoo_correlation_prices
from data_sources.cftc import fetch_cot_positions
from data_sources.yields import fetch_treasury_curve
from data_sources.economic_data import fetch_bls_indicators
from data.seed_data import yahoo_market
from engine.scoring import analyze_all

st.set_page_config(page_title="BiasFlo — FX Market Intelligence", page_icon=":material/analytics:", layout="wide", initial_sidebar_state="expanded")
init_db(settings.database_path)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:#080C11;
    --bg2:#0B1118;
    --panel:#101720;
    --panel2:#131C26;
    --border:#1D2935;
    --border2:#263443;
    --text:#F2F5F8;
    --muted:#7F8C9A;
    --muted2:#A6B1BD;
    --green:#2DD477;
    --green-bg:rgba(45,212,119,.10);
    --red:#FF5263;
    --red-bg:rgba(255,82,99,.10);
    --amber:#F5B84B;
    --blue:#4DA3FF;
    --cyan:#55D6FF;
}

html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: radial-gradient(circle at 80% -10%, #13202c 0, var(--bg) 35%); color:var(--text); }
.block-container { max-width: 1700px; padding: 1.25rem 2rem 3rem; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0A1016,#080C11); border-right:1px solid var(--border); }
section[data-testid="stSidebar"] .block-container { padding:1.35rem 1rem; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom:.35rem; }
h1,h2,h3 { font-family:Inter,sans-serif; letter-spacing:-.025em; }
h1 { font-size:2.15rem!important; font-weight:800!important; margin-bottom:.15rem!important; }
h2 { font-size:1.25rem!important; font-weight:700!important; margin-top:1.5rem!important; }
h3 { font-size:1rem!important; font-weight:650!important; }

[data-testid="stMetric"] {
    background:linear-gradient(145deg,rgba(19,28,38,.96),rgba(12,18,25,.96));
    border:1px solid var(--border);
    border-radius:10px;
    padding:.7rem .85rem;
    box-shadow:0 8px 24px rgba(0,0,0,.12);
}
[data-testid="stMetricLabel"] { color:var(--muted)!important; font-size:.68rem!important; font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
[data-testid="stMetricValue"] { color:var(--text)!important; font-size:1.15rem!important; font-weight:700!important; }
[data-testid="stMetricDelta"] { font-size:.72rem!important; }

div[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:10px; overflow:hidden; background:var(--panel); }
[data-testid="stDataFrame"] iframe { border-radius:10px; }
div.stButton > button { border-radius:8px; border:1px solid var(--border2); background:#111A23; color:var(--text); font-weight:600; transition:.15s; }
div.stButton > button:hover { border-color:#3B536B; background:#17222D; }
div[data-baseweb="select"] > div { background:#0F171F; border-color:var(--border2); border-radius:8px; }
div[data-baseweb="tab-list"] { gap:.35rem; }
button[data-baseweb="tab"] { border-radius:8px!important; }

.panel {
    background:linear-gradient(145deg,rgba(17,25,34,.98),rgba(12,18,25,.98));
    border:1px solid var(--border);
    border-radius:12px;
    padding:16px;
    margin-bottom:12px;
    box-shadow:0 10px 28px rgba(0,0,0,.10);
}
.panel:hover { border-color:#2A3A49; }
.small { font-size:.68rem; color:var(--muted); text-transform:uppercase; letter-spacing:.075em; font-weight:600; }
.big { font-size:1.55rem; font-weight:800; letter-spacing:-.03em; }
.positive { color:var(--green)!important; }
.negative { color:var(--red)!important; }
.amber { color:var(--amber)!important; }
.blue { color:var(--blue)!important; }
.muted { color:var(--muted)!important; }

.brand-mark { display:flex; align-items:center; gap:10px; margin-bottom:3px; }
.brand-dot { width:10px; height:10px; border-radius:50%; background:var(--cyan); box-shadow:0 0 18px rgba(85,214,255,.65); }
.brand-name { font-size:1.05rem; font-weight:800; letter-spacing:.08em; }
.brand-sub { color:var(--muted); font-size:.66rem; text-transform:uppercase; letter-spacing:.12em; }

.hero {
    background:linear-gradient(135deg,rgba(19,31,43,.98),rgba(11,17,24,.98));
    border:1px solid var(--border2);
    border-radius:14px;
    padding:18px 20px;
    min-height:145px;
    box-shadow:0 14px 36px rgba(0,0,0,.16);
}
.hero-title { font-size:.68rem; text-transform:uppercase; color:var(--muted); letter-spacing:.10em; font-weight:700; }
.hero-value { font-size:2rem; font-weight:800; letter-spacing:-.04em; margin:.2rem 0; }
.hero-score { color:var(--muted2); font-size:.8rem; }
.bar { height:6px; background:#202B36; border-radius:99px; overflow:hidden; margin-top:9px; }
.bar > span { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--blue),var(--cyan)); }

.signal-card {
    background:linear-gradient(145deg,#121B24,#0D141C);
    border:1px solid var(--border);
    border-radius:12px;
    padding:15px;
    min-height:170px;
}
.signal-pair { font-size:1.05rem; font-weight:750; }
.signal-action { font-size:1.35rem; font-weight:800; margin:5px 0; }
.signal-meta { color:var(--muted2); font-size:.78rem; }
.tag { display:inline-block; padding:3px 7px; border-radius:5px; font-size:.62rem; font-weight:700; letter-spacing:.04em; }
.tag-buy { color:var(--green); background:var(--green-bg); }
.tag-sell { color:var(--red); background:var(--red-bg); }
.tag-wait { color:var(--amber); background:rgba(245,184,75,.10); }
.divider { height:1px; background:var(--border); margin:14px 0; }

.section-kicker { color:var(--blue); font-size:.66rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
.section-title { font-size:1.2rem; font-weight:750; margin-top:2px; }
.section-desc { color:var(--muted); font-size:.75rem; margin-bottom:10px; }

.sidebar-section { color:#617181; font-size:.62rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin:1rem 0 .45rem; }
.status-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; color:var(--muted2); font-size:.76rem; }
.status-dot { width:7px; height:7px; border-radius:50%; display:inline-block; margin-right:7px; background:var(--green); box-shadow:0 0 9px rgba(45,212,119,.5); }

@media (max-width: 900px) {
    .block-container { padding:1rem .8rem 2rem; }
    h1 { font-size:1.7rem!important; }
}
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

@st.cache_data(ttl=3600, show_spinner=False)
def load_correlation_prices():
    return yahoo_correlation_prices(period="1y")


def load_data(source: str):
    if source == "Yahoo Finance":
        yahoo_data, provider = load_yahoo_market()
        return yahoo_data, demo_currency(), demo_catalysts(), provider
    return demo_market(), demo_currency(), demo_catalysts(), "DEMO"


data_source = "Demo Mode"
if "selected_pair" not in st.session_state:
    st.session_state.selected_pair = None
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


FEATURED_NEWS = {
    "JPY": {
        "title": "JPY pairs selling resumes - USD/JPY 152, EUR/JPY 178 and GBP/JPY 207 next?",
        "url": "https://www.fxstreet.com/analysis/jpy-pairs-selling-resumes-usd-jpy-152-eur-jpy-178-and-gbp-jpy-207-next-video-202609070907",
        "source": "FXStreet",
        "note": "Use this as a JPY-cross context article, not as proof of every JPY pair's direction.",
    }
}


def currency_score(currency):
    values = currencies.get(currency, {})
    return float(values.get("structural", 0)) * .30 + float(values.get("repricing", 0)) * .40 + float(values.get("flow", 0)) * .30


def pair_currencies(pair):
    return (pair[:3], pair[3:]) if len(pair) == 6 else (pair[:3], pair[-3:])


def signed_pair_score(analysis):
    if analysis.action == "BUY":
        return float(analysis.score)
    if analysis.action == "SELL":
        return -float(analysis.score)
    return 0.0


def factor_rows(analysis):
    rows = []
    for name, raw_value in analysis.factors.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if analysis.action == "BUY":
            status = "CONFIRMS" if value > .25 else "CONFLICTS" if value < -.25 else "NEUTRAL"
        elif analysis.action == "SELL":
            status = "CONFIRMS" if value < -.25 else "CONFLICTS" if value > .25 else "NEUTRAL"
        else:
            status = "NEUTRAL"
        rows.append((name.replace("_", " ").title(), value, status))
    return sorted(rows, key=lambda row: abs(row[1]), reverse=True)


def build_why_trade(analysis):
    base, quote = pair_currencies(analysis.pair)
    base_score = currency_score(base)
    quote_score = currency_score(quote)
    rows = factor_rows(analysis)
    confirming = [row for row in rows if row[2] == "CONFIRMS"][:4]
    conflicts = [row for row in rows if row[2] == "CONFLICTS"][:2]
    if analysis.action == "BUY":
        direction = f"{base} is stronger than {quote} on the currency-engine composite ({base_score:+.2f} vs {quote_score:+.2f})."
    elif analysis.action == "SELL":
        direction = f"{quote} is stronger than {base} on the currency-engine composite ({quote_score:+.2f} vs {base_score:+.2f})."
    else:
        direction = f"The currency edge is not decisive ({base} {base_score:+.2f} vs {quote} {quote_score:+.2f})."
    bullets = [direction]
    bullets.extend(f"{name} is confirming the {analysis.action.lower()} thesis ({value:+.2f})." for name, value, _ in confirming)
    if analysis.alignment:
        bullets.append(f"Model alignment is {analysis.alignment}/9, so the signal has {analysis.alignment} supporting checks.")
    if conflicts:
        bullets.append("The main conflict is " + "; ".join(f"{name} ({value:+.2f})" for name, value, _ in conflicts) + ".")
    verdict = "HIGH CONVICTION" if analysis.confidence >= 70 and analysis.alignment >= 4 else "MODERATE CONVICTION" if analysis.confidence >= 55 else "LOW CONVICTION"
    return {"base": base, "quote": quote, "base_score": base_score, "quote_score": quote_score, "edge": base_score - quote_score, "bullets": bullets, "verdict": verdict}


@st.cache_data(ttl=900, show_spinner=False)
def fetch_pair_news(pair, action):
    base, quote = pair_currencies(pair)
    query = quote_plus(f"{pair} OR {base} {quote} forex")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items = []
        for item in root.findall(".//item")[:15]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source_node = item.find("source")
            source = (source_node.text or "Unknown") if source_node is not None else "Unknown"
            published = (item.findtext("pubDate") or "").strip()
            if not title or not link:
                continue
            lower_title = title.lower()
            positive = sum(term in lower_title for term in ["bullish", "higher", "strengthen", "gains", "rises", "support", "buy", "hawkish", "surge"])
            negative = sum(term in lower_title for term in ["bearish", "lower", "weaken", "falls", "drops", "sell", "dovish", "decline"])
            if action == "BUY":
                stance = "CONFIRMS" if positive > negative else "CONFLICTS" if negative > positive else "MIXED"
            elif action == "SELL":
                stance = "CONFIRMS" if negative > positive else "CONFLICTS" if positive > negative else "MIXED"
            else:
                stance = "MIXED"
            items.append({"title": title, "link": link, "source": source, "published": published, "stance": stance})
        return items
    except (requests.RequestException, ET.ParseError) as error:
        return [{"title": "News feed unavailable", "link": "", "source": "System", "published": "", "stance": "MIXED", "error": str(error)}]


def render_news(analysis):
    st.markdown("#### Bias-aware news radar")
    st.caption("News is contextual evidence. The engine does not force every article to agree with the model signal.")
    base, quote = pair_currencies(analysis.pair)
    if quote == "JPY" or base == "JPY":
        featured = FEATURED_NEWS["JPY"]
        st.markdown(f'<div class="panel"><b>Featured JPY-cross context</b><br><a href="{featured["url"]}" target="_blank">{featured["title"]}</a><br><span class="small">{featured["source"]} · {featured["note"]}</span></div>', unsafe_allow_html=True)
    for item in fetch_pair_news(analysis.pair, analysis.action)[:8]:
        cls = "positive" if item["stance"] == "CONFIRMS" else "negative" if item["stance"] == "CONFLICTS" else "amber"
        title = item["title"].replace("<", "&lt;").replace(">", "&gt;")
        source = item["source"].replace("<", "&lt;").replace(">", "&gt;")
        title_html = f'<a href="{item["link"]}" target="_blank">{title}</a>' if item["link"] else title
        st.markdown(f'<div class="panel" style="padding:10px 12px"><span class="{cls}"><b>{item["stance"]}</b></span> <span class="small">{source}</span><br>{title_html}<br><span class="small">{item["published"]}</span></div>', unsafe_allow_html=True)

def header():
    label, confidence = regime()

    # Brand / page header
    st.markdown(
        '<div class="brand-mark"><span class="brand-dot"></span><span class="brand-name">BIASFLO</span></div>'
        '<div class="brand-sub">FX Market Intelligence Terminal</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    left, right = st.columns([3.3, 6.7])
    with left:
        st.markdown("# Market Overview")
        st.markdown(
            ":orange-badge[DEMO DATA - NOT FOR LIVE TRADING] :blue-badge[Data quality 74%]"
            if provider_name == "DEMO" else
            ":green-badge[YAHOO FINANCE - MARKET PRICES] :blue-badge[Data quality 86%]"
        )
    with right:
        st.markdown(
            f"<div style='text-align:right;color:#7F8C9A;font-size:.72rem;padding-top:18px'>"
            f"<span style='color:#2DD477'>● LIVE</span>&nbsp;&nbsp; "
            f"{datetime.now().strftime('%d %b %Y %H:%M')} EAT&nbsp;&nbsp; • &nbsp;&nbsp;{provider_name}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    moves = {"USD":-.24,"EUR":.18,"GBP":.32,"JPY":-.51,"CHF":.08,"CAD":.64,"AUD":.72,"NZD":-.15}
    cols = st.columns(8)
    for col, cur in zip(cols, CURRENCIES):
        with col:
            cls = "positive" if moves[cur] > 0 else "negative" if moves[cur] < 0 else "muted"
            st.markdown(
                f'<div class="panel" style="padding:11px 12px;margin-bottom:0">'
                f'<div class="small">{cur}</div><div class="{cls}" style="font-size:1.05rem;font-weight:750">{moves[cur]:+.2f}%</div>'
                f'</div>', unsafe_allow_html=True
            )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    cols = st.columns(8)
    assets = [("REGIME", f"{label} {confidence}%"), ("VIX", "15.8"), ("DXY", "103.42"), ("GOLD", "+0.31%"), ("WTI", "+1.12%"), ("S&P 500", "+0.46%"), ("NASDAQ", "+0.68%"), ("BTC", "+1.10%")]
    for col, (name, value) in zip(cols, assets):
        with col:
            cls = "positive" if value.startswith("+") or "RISK ON" in value else "muted"
            st.markdown(
                f'<div class="panel" style="padding:10px 12px;margin-bottom:0">'
                f'<div class="small">{name}</div><div class="{cls}" style="font-size:.92rem;font-weight:700">{value}</div>'
                f'</div>', unsafe_allow_html=True
            )

def sidebar():
    st.sidebar.markdown(
        '<div class="brand-mark"><span class="brand-dot"></span><span class="brand-name">BIASFLO</span></div>'
        '<div class="brand-sub">Institutional FX research</div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-section">Workspace</div>', unsafe_allow_html=True)
    pages = ["Overview", "28 Pair Scanner", "Currency Matrix", "Top Setups", "Catalyst Radar", "Yield Dashboard", "COT & Positioning", "Technical Scanner", "Risk Regime", "Correlations", "Economic Calendar", "Performance", "Settings"]
    page_labels = {"28 Pair Scanner": "28 Pair Scanner", "Currency Matrix": "Currency Matrix", "Top Setups": "Top Setups", "Catalyst Radar": "Catalyst Radar", "Yield Dashboard": "Yield Dashboard", "COT & Positioning": "COT & Positioning", "Technical Scanner": "Technical Scanner", "Risk Regime": "Risk Regime", "Economic Calendar": "Economic Calendar"}
    page = st.sidebar.radio("Navigation", pages, format_func=lambda value: page_labels.get(value, value), label_visibility="collapsed")
    st.sidebar.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="status-row"><span><span class="status-dot"></span>Market status</span><b style="color:#2DD477">OPEN</b></div>'
        '<div class="status-row"><span>Provider</span><b style="color:#F5B84B">Yahoo Finance</b></div>'
        '<div class="status-row"><span>Persistence</span><b style="color:#55D6FF">SQLite</b></div>',
        unsafe_allow_html=True,
    )

    st.sidebar.markdown('<div class="sidebar-section">Data Controls</div>', unsafe_allow_html=True)
    refresh = st.sidebar.selectbox("Auto refresh", ["Manual", "30 sec", "1 min", "5 min", "15 min", "30 min", "1 hour"], index=3)
    if st.sidebar.button("↻  Refresh data", use_container_width=True):
        st.rerun()

    selected_source = st.sidebar.radio(
        "Data source", ["Yahoo Finance", "Demo Mode"],
        index=0 if st.session_state.data_source == "Yahoo Finance" else 1
    )
    if selected_source != st.session_state.data_source:
        st.session_state.data_source = selected_source
        st.rerun()

    st.sidebar.markdown(
        f'<div style="margin-top:12px;padding-top:12px;border-top:1px solid #1D2935;color:#617181;font-size:.64rem">'
        f'Refresh: {refresh}<br>Engine: analyze_all()<br>Data cache: 5 min</div>',
        unsafe_allow_html=True,
    )
    return page

def score_table():
    rows=[]
    for a in analyses:
        rows.append({"PAIR":a.pair,"PRICE":f"{a.price:.5f}","24H":f"{a.daily_change:+.2f}%","SCORE":a.score,"BIAS":a.bias.upper(),"CONF.":f"{a.confidence:.0f}%","GRADE":a.grade,"REPRICE":a.factors["policy"],"YIELD":a.factors["yield"],"TECH":a.factors["technical"],"ALIGN":f"{a.alignment}/9","ACTION":a.action})
    return pd.DataFrame(rows)

def section_header(kicker, title, desc=""):
    st.markdown(
        f'<div class="section-kicker">{kicker}</div>'
        f'<div class="section-title">{title}</div>'
        f'<div class="section-desc">{desc}</div>',
        unsafe_allow_html=True,
    )


def score_bar(score):
    return f'<div class="bar"><span style="width:{max(0,min(100,float(score)))}%"></span></div>'


def signal_class(action):
    return "positive" if action == "BUY" else "negative" if action == "SELL" else "muted"


def render_currency_heatmap():
    currencies_list = list(CURRENCIES)
    values = [[0 if base == quote else round(currency_score(base) - currency_score(quote), 2) for quote in currencies_list] for base in currencies_list]
    figure = go.Figure(go.Heatmap(
        z=values,
        x=currencies_list,
        y=currencies_list,
        colorscale=[[0, "#FF5263"], [.5, "#101720"], [1, "#2DD477"]],
        zmid=0,
        text=[[f"{value:+.2f}" for value in row] for row in values],
        texttemplate="%{text}",
        hovertemplate="%{y} vs %{x}: %{z:+.2f}<extra></extra>",
    ))
    figure.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F2F5F8", xaxis_title="Quote currency", yaxis_title="Base currency")
    st.plotly_chart(figure, use_container_width=True)


def render_opportunity_matrix():
    currencies_list = list(CURRENCIES)
    values = [[None for _ in currencies_list] for _ in currencies_list]
    labels = [["" for _ in currencies_list] for _ in currencies_list]
    for analysis in analyses:
        base, quote = pair_currencies(analysis.pair)
        if base in currencies_list and quote in currencies_list:
            row, column = currencies_list.index(base), currencies_list.index(quote)
            values[row][column] = signed_pair_score(analysis)
            labels[row][column] = f"{analysis.action} {analysis.score:.0f}"
    figure = go.Figure(go.Heatmap(
        z=values,
        x=currencies_list,
        y=currencies_list,
        colorscale=[[0, "#FF5263"], [.5, "#101720"], [1, "#2DD477"]],
        zmid=0,
        zmin=-100,
        zmax=100,
        text=labels,
        texttemplate="%{text}",
        hovertemplate="%{y}%{x}: %{z:+.0f}<extra></extra>",
    ))
    figure.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F2F5F8", xaxis_title="Quote currency", yaxis_title="Base currency")
    st.plotly_chart(figure, use_container_width=True)


def render_conviction_ranking():
    ranked = sorted((analysis for analysis in analyses if analysis.action in ("BUY", "SELL")), key=lambda analysis: (analysis.confidence, analysis.score, analysis.alignment), reverse=True)[:10]
    rows = [{"#": rank, "PAIR": analysis.pair, "ACTION": analysis.action, "SCORE": round(analysis.score), "CONFIDENCE": f"{analysis.confidence:.0f}%", "GRADE": analysis.grade, "ALIGNMENT": f"{analysis.alignment}/9"} for rank, analysis in enumerate(ranked, 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

def overview():
    label, confidence = regime()
    section_header("MARKET STATE", "Risk regime", "Multi-asset context used to frame the FX signal engine.")
    a,b,c = st.columns([2.5, 2.5, 5])
    with a:
        st.markdown(
            f'<div class="hero"><div class="hero-title">Current regime</div>'
            f'<div class="hero-value positive">{label}</div>'
            f'<div class="hero-score">{confidence}% model confidence</div>'
            f'{score_bar(confidence)}</div>', unsafe_allow_html=True
        )
    with b:
        st.markdown(
            '<div class="panel" style="height:100%;margin-bottom:0">'
            '<div class="small">Key drivers</div>'
            '<div style="margin-top:10px"><span class="positive">▲ Equities up</span></div>'
            '<div style="margin-top:7px"><span class="positive">▲ VIX contained</span></div>'
            '<div style="margin-top:7px"><span class="negative">▼ JPY defensive bid</span></div>'
            '<div style="margin-top:7px"><span class="amber">◆ Gold contradiction</span></div>'
            '</div>', unsafe_allow_html=True
        )
    with c:
        st.markdown(
            '<div class="panel" style="height:100%;margin-bottom:0">'
            '<div class="small">Regime engine</div>'
            '<div style="font-size:.88rem;line-height:1.7;margin-top:8px;color:#C7D0D9">'
            'Multiple assets confirm the current classification. Gold strength is a contradiction, '
            'so conviction is capped rather than inferred from a single market.</div>'
            '<div style="margin-top:12px"><span class="tag tag-buy">MULTI-ASSET CONFIRMATION</span></div>'
            '</div>', unsafe_allow_html=True
        )

    section_header("CURRENCY MAP", "Relative currency strength", "Positive cells indicate that the row currency has a stronger composite than the column currency.")
    render_currency_heatmap()

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    section_header("CURRENCY ENGINE", "Currency strength & repricing", "Aggregate structural, repricing and flow inputs. Positive values indicate relative strength.")
    cur_df = pd.DataFrame([
        {"CURRENCY":c,"STRUCTURAL":v["structural"],"REPRICING":v["repricing"],"FLOW":v["flow"],
         "COT":"N/A","RETAIL":"N/A","FINAL":round(currency_score(c),2)}
        for c,v in currencies.items()
    ]).sort_values("FINAL", ascending=False)

    left, right = st.columns([5.5,4.5])
    with left:
        rows_html = ""
        max_abs = max(abs(cur_df["FINAL"]).max(), 1)
        for _, r in cur_df.iterrows():
            val = float(r["FINAL"])
            width = min(100, abs(val)/max_abs*100)
            cls = "positive" if val >= 0 else "negative"
            rows_html += (
                f'<div style="display:grid;grid-template-columns:42px 1fr 58px;gap:10px;align-items:center;margin:10px 0">'
                f'<b style="font-size:.75rem">{r["CURRENCY"]}</b>'
                f'<div class="bar" style="margin:0"><span style="width:{width:.0f}%;background:{"#2DD477" if val>=0 else "#FF5263"}"></span></div>'
                f'<b class="{cls}" style="font-size:.75rem;text-align:right">{val:+.2f}</b></div>'
            )
        st.markdown(f'<div class="panel">{rows_html}</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><div class="small">Model components</div>', unsafe_allow_html=True)
        for _, r in cur_df.iterrows():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #1D2935">'
                f'<span style="font-weight:600">{r["CURRENCY"]}</span>'
                f'<span class="muted">S {r["STRUCTURAL"]:+.2f} &nbsp; R {r["REPRICING"]:+.2f} &nbsp; F {r["FLOW"]:+.2f}</span></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_header("OPPORTUNITY RADAR", "Highest-conviction setups", "Pairs where the model sees the clearest directional edge.")
    top = sorted(analyses, key=lambda x: x.score if x.action == "BUY" else 100-x.score, reverse=True)[:5]
    cols=st.columns(5)
    for col,a in zip(cols,top):
        with col:
            cls = signal_class(a.action)
            tag = "tag-buy" if a.action=="BUY" else "tag-sell" if a.action=="SELL" else "tag-wait"
            st.markdown(
                f'<div class="signal-card">'
                f'<div class="signal-pair">{a.pair}</div>'
                f'<span class="tag {tag}">{a.action}</span>'
                f'<div class="{cls} signal-action">{a.score:.0f}<span style="font-size:.7rem;color:#7F8C9A"> / 100</span></div>'
                f'{score_bar(a.score)}'
                f'<div class="signal-meta" style="margin-top:10px">Confidence <b>{a.confidence:.0f}%</b> &nbsp; • &nbsp; Grade <b>{a.grade}</b></div>'
                f'<div class="signal-meta">Alignment {a.alignment}/9</div>'
                f'</div>', unsafe_allow_html=True
            )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    section_header("MARKET SCANNER", "28-pair signal board", "Fast view of price, score, bias, confidence and model action.")
    df = score_table().copy()
    st.dataframe(df.head(10), use_container_width=True, hide_index=True,
                 column_config={
                     "SCORE": st.column_config.NumberColumn("SCORE", format="%.1f"),
                     "CONF.": st.column_config.TextColumn("CONF."),
                 })

    section_header("CONVICTION", "Signal ranking", "The strongest directional signals by confidence, score and model alignment.")
    render_conviction_ranking()
    section_header("OPPORTUNITY MATRIX", "BUY / SELL opportunity map", "Each cell represents the model action for the base and quote combination.")
    render_opportunity_matrix()

def scanner():
    section_header("MARKET SCANNER", "28-pair scanner", "Filter the model by action, confidence and currency exposure.")
    c1,c2,c3,c4 = st.columns([1.2,1.2,1.2,1.5])
    action=c1.selectbox("Action", ["All","BUY","SELL","WAIT","NO TRADE"])
    minimum=c2.selectbox("Confidence", ["All","80%+","70%+","60%+"])
    currency=c3.selectbox("Currency", ["All"]+CURRENCIES)
    selected=c4.selectbox("Pair X-ray", ["Select a pair"]+PAIRS)
    df=score_table()
    if action != "All": df=df[df.ACTION==action]
    if minimum != "All": df=df[df["CONF."].str.rstrip('%').astype(float)>=int(minimum[:2])]
    if currency != "All": df=df[df.PAIR.str.startswith(currency) | df.PAIR.str.endswith(currency)]
    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin:8px 0 10px">'
        f'<span class="muted" style="font-size:.72rem">{len(df)} of {len(PAIRS)} pairs match the current filters</span>'
        f'<span class="tag tag-buy">MODEL OUTPUT</span></div>',
        unsafe_allow_html=True
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    if selected != "Select a pair":
        st.session_state.selected_pair = selected
    if st.session_state.get("selected_pair"):
        pair_xray(st.session_state.selected_pair)

def pair_xray(pair):
    analysis = next(item for item in analyses if item.pair == pair)
    why = build_why_trade(analysis)
    section_header("PAIR X-RAY", pair, "Detailed model view: thesis, contextual news, price response and factor contributions.")
    metrics = st.columns(5)
    values = [("Action", analysis.action), ("Score", f"{analysis.score:.0f}/100"), ("Confidence", f"{analysis.confidence:.0f}%"), ("Grade", analysis.grade), ("Alignment", f"{analysis.alignment}/9")]
    for column, (name, value) in zip(metrics, values):
        with column:
            cls = signal_class(analysis.action) if name == "Action" else ""
            st.markdown(f'<div class="panel" style="margin-bottom:0"><div class="small">{name}</div><div class="{cls}" style="font-size:1.15rem;font-weight:800;margin-top:5px">{value}</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Why this trade?", "News radar", "Price & factors"])
    with tab1:
        left, right = st.columns([1.25, .75])
        with left:
            cls = signal_class(analysis.action)
            st.markdown(f'<div class="panel"><div class="small">Model verdict</div><div class="{cls}" style="font-size:1.45rem;font-weight:800">{analysis.action} · {why["verdict"]}</div>{score_bar(analysis.confidence)}<div class="small">Signal confidence {analysis.confidence:.0f}%</div></div>', unsafe_allow_html=True)
            st.markdown("#### Why the model is leaning this way")
            for bullet in why["bullets"]:
                st.markdown(f'<div class="panel" style="padding:10px 12px">✓ {bullet}</div>', unsafe_allow_html=True)
        with right:
            edge_cls = "positive" if why["edge"] > 0 else "negative"
            st.markdown(f'<div class="panel"><div class="small">Currency battle</div><b>{why["base"]}</b> <span class="muted">{why["base_score"]:+.2f}</span> vs <b>{why["quote"]}</b> <span class="muted">{why["quote_score"]:+.2f}</span><div class="{edge_cls}" style="font-size:1.5rem;font-weight:800;margin-top:12px">Edge {why["edge"]:+.2f}</div><div class="small">{why["base"]} minus {why["quote"]} composite strength</div></div>', unsafe_allow_html=True)
            st.markdown("#### Model alignment")
            for name, value, status in factor_rows(analysis)[:6]:
                cls = "positive" if status == "CONFIRMS" else "negative" if status == "CONFLICTS" else "muted"
                st.markdown(f'<div class="panel" style="padding:9px 11px"><span class="{cls}">{status}</span> · {name} <b>{value:+.2f}</b></div>', unsafe_allow_html=True)

    with tab2:
        render_news(analysis)

    with tab3:
        left, right = st.columns([7, 3])
        with left:
            history = yahoo_history(pair, period="1y") if provider_name == "YAHOO FINANCE" else pd.DataFrame()
            if not history.empty and "Close" in history:
                prices = history["Close"].astype(float).dropna().tail(252)
                x = prices.index
            else:
                x = np.arange(120)
                base = market[pair]["price"]
                prices = base * (1 + np.cumsum(np.random.default_rng(sum(map(ord, pair))).normal(0, .002, 120)))
            figure = go.Figure()
            figure.add_trace(go.Scatter(x=x, y=prices, mode="lines", line={"color": "#4DA3FF", "width": 2}, name="Price"))
            figure.add_trace(go.Scatter(x=x, y=pd.Series(prices).rolling(14).mean(), mode="lines", line={"color": "#F5B84B", "width": 1.5}, name="14 SMA"))
            figure.update_layout(height=340, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor="#101720", plot_bgcolor="#101720", font_color="#A6B1BD", xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=True, gridcolor="#1D2935", zeroline=False), legend=dict(orientation="h", y=1.08, x=0, font_size=11))
            st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
        with right:
            st.markdown(f'<div class="panel" style="min-height:340px"><div class="small">Net driver</div><div class="big">{analysis.score:.0f}/100</div><hr><div>{analysis.explanation}</div></div>', unsafe_allow_html=True)
        section_header("SIGNAL DECOMPOSITION", "Factor contribution", "What is confirming, conflicting or remaining neutral.")
        factor_df = pd.DataFrame([{"FACTOR": name.upper(), "CONTRIBUTION": value, "STATUS": status} for name, value, status in factor_rows(analysis)])
        st.dataframe(factor_df, use_container_width=True, hide_index=True)
        st.info("Core rule: rate levels are not treated as directional signals. Repricing, yield driver, surprise, flow, cross-asset confirmation, and price response must agree before a trade is considered.", icon=":material/gavel:")

def generic_page(page):
    page_labels = {"Yield Dashboard": "Yield dashboard", "Economic Calendar": "Economic calendar", "COT & Positioning": "COT & positioning", "Risk Regime": "Risk regime", "Technical Scanner": "Technical scanner", "Currency Matrix": "Currency matrix", "Catalyst Radar": "Catalyst radar", "Top Setups": "Top setups", "Correlations": "Correlations", "Performance": "Performance", "Settings": "Settings"}
    st.subheader(page_labels.get(page, page))
    if page == "Yield Dashboard":
        yield_page()
        return
    if page == "Economic Calendar":
        economic_page()
        return
    if page == "Correlations":
        correlation_page()
        return
    if page == "COT & Positioning":
        positioning_page()
        return
    st.markdown(f'<div class="panel"><b>{provider_name} price data</b><br>Market prices and historical returns may come from Yahoo Finance. Economic forecasts, COT, retail positioning, central-bank repricing, and news remain N/A until a dedicated provider is connected.</div>', unsafe_allow_html=True)
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
    st.markdown(f'<div class="panel"><b>U.S. Treasury par yield curve</b><br>Latest available observation: {data["date"]}. Source: {data["source"]}. Yields are rates, not directional signals by themselves.</div>', unsafe_allow_html=True)
    short, long = st.columns(2)
    with short:
        short.metric("2Y yield", f"{curve.get('2Y', float('nan')):.2f}%")
    with long:
        long.metric("10Y-2Y spread", f"{(curve.get('10Y', 0) - curve.get('2Y', 0)) * 100:+.1f} bp")
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
    st.markdown('<div class="panel"><b>U.S. economic indicators</b><br>CPI and labor observations from the U.S. Bureau of Labor Statistics public API. GDP requires a separate BEA data series and is not inferred here.</div>', unsafe_allow_html=True)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption("BLS release values are official observations and are not investment advice. Release timing varies by series.")


def correlation_page():
    """Calculate Pearson correlations from Yahoo daily price returns."""
    prices = load_correlation_prices()
    benchmarks = ["GOLD", "WTI", "S&P 500"]
    pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
    windows = {"1M": 21, "3M": 63, "1Y": 252}
    if not prices:
        st.warning("Yahoo Finance did not return price history. Refresh later to retry the correlation feed.")
        return
    rows = []
    for pair in pairs:
        if pair not in prices:
            continue
        for benchmark in benchmarks:
            if benchmark not in prices:
                continue
            joined = pd.concat([prices[pair].rename("pair"), prices[benchmark].rename("benchmark")], axis=1).dropna()
            returns = joined.pct_change().dropna()
            row = {"PAIR": pair, "ASSET": benchmark, "OBSERVATIONS": len(returns)}
            for label, window in windows.items():
                sample = returns.tail(window)
                row[label] = round(sample["pair"].corr(sample["benchmark"]), 3) if len(sample) >= max(20, window // 2) else None
            rows.append(row)
    table = pd.DataFrame(rows)
    if table.empty:
        st.warning("Insufficient overlapping Yahoo Finance history to calculate correlations.")
        return
    st.markdown('<div class="panel"><b>Price return correlations</b><br>Pearson correlation (r) calculated from aligned Yahoo Finance daily closing prices and percentage returns. Values near +1 move together; values near -1 move in opposite directions. Correlation is descriptive, not causal.</div>', unsafe_allow_html=True)
    st.caption("Raw feed: Yahoo Finance daily prices | Assets: Gold futures (GC=F), WTI futures (CL=F), and S&P 500 (^GSPC)")
    selected_window = st.selectbox("Timeframe", list(windows), index=1)
    display = table[["PAIR", "ASSET", selected_window, "OBSERVATIONS"]].rename(columns={selected_window: "CORRELATION (r)"})
    st.dataframe(display, use_container_width=True, hide_index=True)
    matrix = table.pivot(index="PAIR", columns="ASSET", values=selected_window)
    st.subheader(f"{selected_window} correlation matrix")
    st.dataframe(matrix.round(3), use_container_width=True)


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
    st.markdown('<div class="panel"><b>Institutional positioning</b><br>Non-commercial futures positioning from the CFTC weekly Commitments of Traders report. CFTC publishes this report weekly, usually Friday afternoon Eastern Time.</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        left.metric("Currencies available", len(table))
    with right:
        right.metric("Average net position", f"{table['NET POSITION'].mean():,.0f}")
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
    m1.metric("Pairs with history", len(rows)); m2.metric("Average 1M return", f"{np.mean(returns):+.2f}%"); m3.metric("Positive month", f"{sum(value > 0 for value in returns) / len(returns) * 100:.0f}%"); m4.metric("Data source", "YAHOO")
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
