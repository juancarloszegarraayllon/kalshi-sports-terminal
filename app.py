import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

# 1. Page Config
st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# 2. CSS Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;color:#f0f0ff!important;font-size:2.2rem!important;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px;flex:1;text-align:center;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;}
.metric-value{font-size:22px;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px;transition:0.2s;}
.market-card:hover{border-color:#4f46e5;}
.card-title{font-size:14px;color:#e2e8f0;margin-bottom:12px;min-height:50px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;color:#4ade80;border-radius:6px;padding:5px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;color:#f87171;border-radius:6px;padding:5px;text-align:center;}
.cat-pill{font-size:10px;padding:3px 10px;border-radius:4px;border:1px solid #3730a3;color:#818cf8;text-transform:uppercase;}
</style>
""", unsafe_allow_html=True)

# 3. Constants & Mappings (Keep your existing SPORT_TAGS and SERIES_TO_SPORT here)
# [Insert your SPORT_TAGS, SPORT_ICON, SERIES_TO_SPORT, detect_sport, SOCCER_COMP_MAP, get_soccer_comp here]
# ... (I am assuming these functions/dicts are present in your script)

# 4. API Client Setup
@st.cache_resource
def get_client():
    if "KALSHI_API_KEY_ID" not in st.secrets:
        st.error("Missing KALSHI_API_KEY_ID in Secrets.")
        st.stop()
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        key_id = st.secrets["KALSHI_API_KEY_ID"]
        key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(key_str)
            pem = f.name
        
        cfg = Configuration()
        cfg.api_key_id = key_id
        cfg.private_key_pem_path = pem
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"Authentication Failed: {e}")
        st.stop()

client = get_client()

# 5. Optimized Pagination
def paginate(with_markets=False, category=None, series_ticker=None, max_pages=1): # Default to 1 for speed
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit": 100, "status": "open"}
            if with_markets: kw["with_nested_markets"] = True
            if category: kw["category"] = category
            if series_ticker: kw["series_ticker"] = series_ticker
            if cursor: kw["cursor"] = cursor
            
            resp = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.2) # Faster sleep
        except Exception as e:
            st.sidebar.warning(f"API Limit: {e}")
            break
    return events

# 6. Data Fetching
@st.cache_data(ttl=300)
def fetch_all():
    prog = st.progress(0, text="📡 Connecting to Kalshi...")
    
    # Step 1: General Events
    all_ev = paginate(with_markets=False, max_pages=5) 
    prog.progress(40, text=f"Found {len(all_ev)} markets. Analyzing sports...")

    # Step 2: Sports Data (Limit to high-interest series for speed)
    ev_map = {e["event_ticker"]: e for e in all_ev}
    
    # Building DataFrame
    if not ev_map:
        prog.empty()
        return pd.DataFrame()

    df = pd.DataFrame(list(ev_map.values()))
    
    # Robust Category Logic
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other")
    df["_series"]  = df.get("series_ticker", pd.Series("", index=df.index)).fillna("")
    df["_sport"]   = df["_series"].apply(lambda x: detect_sport(x) if 'detect_sport' in globals() else "")
    df["_is_sport"] = df["_sport"] != ""

    # FIXED Extract Function
    def extract_prices(row):
        mkts = row.get("markets")
        if not isinstance(mkts, list) or len(mkts) == 0:
            return "—", "—"
        try:
            m = mkts[0]
            # Use safe formatting
            y_val = m.get("yes_bid") or m.get("yes_bid_dollars") or 0
            n_val = m.get("no_bid") or m.get("no_bid_dollars") or 0
            
            def fmt(v): return f"{int(round(float(v)*100))}%" if float(v) <= 1 else f"{int(v)}%"
            return fmt(y_val), fmt(n_val)
        except:
            return "—", "—"

    price_info = df.apply(extract_prices, axis=1, result_type="expand")
    df["_yes"] = price_info[0]
    df["_no"] = price_info[1]

    prog.progress(100)
    prog.empty()
    return df

# 7. Main UI Execution
st.title("📡 Kalshi Terminal")

# This forces the app to show something immediately
with st.spinner("Initializing Data Stream..."):
    df = fetch_all()

if df.empty:
    st.warning("No data returned. Check if Kalshi markets are open or your API Key is correct.")
else:
    # Metric Strip
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-box"><div class="metric-label">Total Markets</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="metric-label">Sports Events</div><div class="metric-value">{df["_is_sport"].sum()}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="metric-label">Status</div><div class="metric-value">LIVE</div></div>', unsafe_allow_html=True)

    # Simple Grid Rendering
    st.markdown("---")
    html_grid = '<div class="card-grid">'
    for _, row in df.head(50).iterrows(): # Show top 50 to ensure fast rendering
        html_grid += f"""
        <div class="market-card">
            <span class="cat-pill">{row['category']}</span>
            <div class="card-title"><b>{row['title']}</b></div>
            <div class="odds-row">
                <div class="odds-yes">YES {row['_yes']}</div>
                <div class="odds-no">NO {row['_no']}</div>
            </div>
        </div>
        """
    html_grid += "</div>"
    st.markdown(html_grid, unsafe_allow_html=True)

# 8. Refresh logic
if st.sidebar.button("Force Refresh"):
    st.cache_data.clear()
    st.rerun()
