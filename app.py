import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# Custom CSS for the Terminal Aesthetic
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#6b7280!important;font-size:11px!important;letter-spacing:.08em;text-transform:uppercase;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;color:#f0f0ff!important;letter-spacing:-.02em;font-size:2.2rem!important;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;position:relative;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.cat-pill{font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:4px;border:1px solid;white-space:nowrap;}
.pill-sports{background:#1a2e1a;color:#4ade80;border-color:#166534;}
.pill-elections{background:#2e1a1e;color:#f472b6;border-color:#9d174d;}
.pill-politics{background:#1e1a2e;color:#818cf8;border-color:#3730a3;}
.pill-economics{background:#2e2a1a;color:#fbbf24;border-color:#92400e;}
.pill-financials{background:#2e2a1a;color:#fb923c;border-color:#9a3412;}
.pill-crypto{background:#1e2a2e;color:#67e8f9;border-color:#0e7490;}
.pill-companies{background:#2e1e2e;color:#d8b4fe;border-color:#7e22ce;}
.pill-entertainment{background:#2e1e1a;color:#fdba74;border-color:#c2410c;}
.pill-climate{background:#1a2e2e;color:#22d3ee;border-color:#164e63;}
.pill-science{background:#1e2e1a;color:#86efac;border-color:#14532d;}
.pill-health{background:#2e1a2e;color:#e879f9;border-color:#701a75;}
.pill-default{background:#1e1e32;color:#94a3b8;border-color:#2d2d55;}
.date-text{font-size:11px;color:#6b7280;}
.card-icon{font-size:20px;margin-bottom:6px;display:block;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.ticker-text{font-size:10px;color:#374151;letter-spacing:.06em;display:block;margin-bottom:8px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;}
.odds-price-yes{font-size:15px;font-weight:500;color:#4ade80;}
.odds-price-no{font-size:15px;font-weight:500;color:#f87171;}
.empty-state{text-align:center;padding:80px 20px;color:#374151;font-size:14px;}
hr{border-color:#1e1e32!important;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1a;border-bottom:1px solid #1e1e32;gap:2px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#4b5563;border:none;font-size:12px;padding:8px 12px;}
.stTabs [aria-selected="true"]{background:#1e1e32!important;color:#a5b4fc!important;border-radius:6px 6px 0 0;}
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),"Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),"Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),"Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),"Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),"Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),"Social":("👥","pill-default"),
    "World":("🌐","pill-default"),"Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

CAT_TAGS = {
    "Elections":["US Elections","International elections","House","Primaries"],
    "Politics":["Trump","Congress","International","SCOTUS & courts","Local","Iran"],
    "Economics":["Fed","Inflation","GDP","Jobs & Economy","Housing","Oil and energy","Global Central Banks"],
    "Financials":["S&P","Nasdaq","Metals","Agriculture","Oil & Gas","Treasuries","EUR/USD","USD/JPY"],
    "Crypto":["BTC","ETH","SOL","DOGE","XRP","BNB","HYPE"],
    "Companies":["IPOs","Elon Musk","CEOs","Product launches","Layoffs"],
    "Entertainment":["Music","Television","Movies","Awards","Video games","Oscars"],
    "Climate and Weather":["Hurricanes","Daily temperature","Snow and rain","Climate change","Natural disasters"],
    "Science and Technology":["AI","Space","Medicine","Energy"],
    "Health":["Diseases"],
    "Mentions":["Earnings","Politicians","Sports"],
}

# (Omitted list for brevity, keeping existing SPORT_TAGS logic)
# [Insert your existing SPORT_TAGS, SPORT_ICON, SERIES_TO_SPORT, detect_sport, SOCCER_COMP_MAP, get_soccer_comp code here]
# ... 

# Utility Functions
def safe_date(val):
    try:
        if val is None or val == "": return None
        if isinstance(val, date) and not isinstance(val, pd.Timestamp): return val
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except: return None

def fmt_date(d):
    try: return d.strftime("%b %d") if d else "Open"
    except: return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f<=1.0 else int(round(f))}%"
    except: return "—"

@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        key_id  = st.secrets["KALSHI_API_KEY_ID"]
        key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(key_str); pem = f.name
        cfg = Configuration()
        cfg.api_key_id = key_id
        cfg.private_key_pem_path = pem
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"❌ {e}"); st.stop()

client = get_client()

def paginate(with_markets=False, category=None, series_ticker=None, max_pages=30):
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit": 200, "status": "open"}
            if with_markets:  kw["with_nested_markets"] = True
            if category:      kw["category"] = category
            if series_ticker: kw["series_ticker"] = series_ticker
            if cursor:        kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.35)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

@st.cache_data(ttl=600)
def fetch_all():
    prog = st.progress(0, text="Step 1 — Fetching all events…")
    all_ev = paginate(with_markets=False, max_pages=30)
    prog.progress(0.3, text=f"{len(all_ev)} events. Step 2 — Fetching sports with odds…")

    # All sport series tickers
    all_sport_series = list(SERIES_TO_SPORT.keys())
    ev_map = {e["event_ticker"]: e for e in all_ev}

    total = len(all_sport_series)
    for i, series in enumerate(all_sport_series):
        prog.progress(0.3 + 0.6*(i/total), text=f"Fetching {series}…")
        batch = paginate(with_markets=True, series_ticker=series, max_pages=3)
        for e in batch:
            t = e.get("event_ticker","")
            if not t: continue
            if t not in ev_map or (e.get("markets") and not ev_map.get(t,{}).get("markets")):
                ev_map[t] = e

    prog.progress(0.95, text="Building dataframe…")
    combined = list(ev_map.values())
    if not combined:
        prog.empty(); return pd.DataFrame()

    df = pd.DataFrame(combined)
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]  = df.get("series_ticker", pd.Series("", index=df.index)).fillna("").str.upper()
    df["_sport"]   = df["_series"].apply(detect_sport)
    df["_is_sport"] = df["_sport"] != ""
    df["_soccer_comp"] = df.apply(lambda r: get_soccer_comp(r["_series"]) if r["_sport"]=="Soccer" else "", axis=1)

    # --- FIXED EXTRACT FUNCTION ---
    def extract(row):
        mkts = row.get("markets")
        
        # Guard against Non-lists or empty lists
        if not isinstance(mkts, list) or len(mkts) == 0:
            return "—", "—", None
        
        try:
            m = mkts[0]
            yes = fmt_pct(m.get("yes_bid_dollars") or m.get("yes_bid"))
            no  = fmt_pct(m.get("no_bid_dollars")  or m.get("no_bid"))
            
            close = None
            for mk in mkts:
                d = safe_date(mk.get("close_time"))
                if d and (close is None or d < close): close = d
            return yes, no, close
        except:
            return "—", "—", None

    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = info[0]; df["_no"] = info[1]; df["_mkt_dt"] = info[2]

    def best_dt(row):
        for col in ["strike_date","close_time","end_date","expiration_time"]:
            d = safe_date(row.get(col))
            if d: return d
        return row.get("_mkt_dt")

    df["_sort_dt"]    = df.apply(best_dt, axis=1)
    df["_display_dt"] = df["_sort_dt"].apply(fmt_date)
    prog.progress(1.0); prog.empty()
    return df

# Sidebar & Rendering Logic 
# (Omitted for space, keeping your existing filtering/tab logic)
# ...
