import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

# --- Streamlit page config ---
st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# --- Custom CSS ---
st.markdown("""
<style>
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;color:#f0f0ff;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;position:relative;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
</style>
""", unsafe_allow_html=True)

# --- Kalshi API Config ---
KALSHI_API_KEY = st.secrets.get("KALSHI_API_KEY")  # store your key in Streamlit secrets
KALSHI_API_URL = "https://api.kalshi.com/v1/markets"

# --- Cache API calls ---
@st.cache_data(ttl=60)
def fetch_markets():
    headers = {"Authorization": f"Bearer {KALSHI_API_KEY}"}
    try:
        resp = requests.get(KALSHI_API_URL, headers=headers, params={"category": "Sports"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("markets", [])
    except Exception as e:
        st.error(f"Error fetching Kalshi markets: {e}")
        return []

# --- Fetch markets ---
markets = fetch_markets()

# --- Metrics strip ---
st.markdown('<div class="metric-strip">', unsafe_allow_html=True)
st.markdown(f'<div class="metric-box"><div class="metric-label">Total Sports Markets</div><div class="metric-value">{len(markets)}</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="metric-box"><div class="metric-label">Last Updated</div><div class="metric-value">{datetime.now(timezone.utc).strftime("%H:%M:%S UTC")}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Market cards ---
if markets:
    st.markdown('<div class="card-grid">', unsafe_allow_html=True)
    for m in markets[:20]:  # show only first 20 for demo
        title = m.get("name", "Unknown Market")
        status = m.get("state", "unknown")
        st.markdown(f"""
        <div class="market-card">
            <div class="card-title">{title}</div>
            <div>Status: {status}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.write("No markets available at the moment.")
