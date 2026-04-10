import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import tempfile

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== YOUR ORIGINAL FULL CSS ======================
st.markdown("""
<style>
/* Paste your ENTIRE original <style> block here - from the very first <style> to the last </style> */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}

/* Title */
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}

/* All your card, outcome, nav, tab styles - copy everything from your original file */
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;}
.market-card{background:#0a0a0a;border:1px solid #1c1c1c;border-radius:10px;padding:16px 18px;transition:border-color .15s,transform .15s;}
.market-card:hover{border-color:#00ff00;transform:translateY(-2px);}
.card-top{display:flex;justify-content:flex-start;align-items:center;margin-bottom:6px;}
.cat-pill{font-size:20px;font-weight:700;letter-spacing:.02em;text-transform:capitalize;padding:0;border:none;background:transparent;white-space:nowrap;color:#ffffff!important;}
.card-timing{display:flex;flex-direction:row;align-items:center;gap:4px;margin-bottom:8px;}
.date-text{font-size:11px;color:#ffffff;opacity:.6;}
.card-icon{font-size:20px;margin-bottom:4px;display:block;}
.card-title{font-size:14px;font-weight:600;color:#ffffff;line-height:1.45;margin-bottom:12px;min-height:52px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1c1c1c;padding-top:10px;}
.ticker-link{font-size:10px;color:#00ff00;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;text-decoration:none;opacity:.6;}
.outcome-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;}
.outcome-label{font-size:11px;color:#ffffff;font-weight:500;flex:0 0 auto;min-width:80px;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.85;}
.outcome-chance{font-size:13px;font-weight:700;color:#ffffff;flex:0 0 auto;min-width:38px;text-align:right;}
.outcome-odds{display:flex;gap:6px;flex:1;justify-content:flex-end;}
.odds-yes{background:#001500;border:1px solid #00ff00;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{background:#150000;border:1px solid #ff2222;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#ffffff;text-transform:uppercase;letter-spacing:.08em;opacity:.5;}
.odds-price-yes{font-size:15px;font-weight:700;color:#00ff00;}
.odds-price-no{font-size:15px;font-weight:700;color:#ff2222;}
.empty-state{text-align:center;padding:80px 20px;color:#333;font-size:14px;}
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ====================== METADATA & DICTIONARIES ======================
# Paste these exactly from your original file:
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials","Crypto","Companies","Entertainment","Climate and Weather","Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = { ... }  # ← your full CAT_META
CAT_TAGS = { ... }  # ← your full CAT_TAGS
SPORT_ICONS = { ... } # ← your full SPORT_ICONS

# CRITICAL: Your big dictionaries
_SPORT_SERIES = { ... }   # ← PASTE YOUR FULL _SPORT_SERIES HERE
SOCCER_COMP = { ... }     # ← PASTE FULL SOCCER_COMP
SPORT_SUBTABS = { ... }   # ← PASTE FULL SPORT_SUBTABS

SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# ====================== HELPERS ======================
def parse_game_date_from_ticker(event_ticker):
    import re
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = str(event_ticker).split("-")
        if len(parts) < 2: return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m: return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        return date(2000 + int(yy), MONTHS.get(mon), int(dd))
    except:
        return None

def fmt_date(d):
    try:
        if not d: return ""
        if hasattr(d, 'hour'):
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} ET"
        return d.strftime("%b %d")
    except:
        return ""

# ====================== CLIENT ======================
@st.cache_resource
def get_client():
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

client = get_client()

# ====================== FAST FETCH ======================
@st.cache_data(ttl=900)
def fetch_all():
    events = []
    cursor = None
    for _ in range(25):
        try:
            resp = client.get_events(limit=200, status="open", with_nested_markets=True, cursor=cursor).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.03)
        except:
            break
    return pd.DataFrame(events)

# ====================== FAST PROCESSING ======================
@st.cache_data(ttl=900)
def process_markets(df):
    if df.empty: return df

    def extract(row):
        mkts = row.get("markets", [])
        if not mkts:
            return None, None, "", []
        first = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport = row.get("_sport", "")

        game_date = parse_game_date_from_ticker(event_ticker)
        exp_dt = None
        try:
            ts = pd.to_datetime(first.get("expected_expiration_time"), utc=True)
            if not pd.isna(ts):
                exp_dt = ts.to_pydatetime().astimezone(UTC)
        except:
            pass

        kickoff_dt = None
        if game_date and sport:
            hours = {"Soccer":2,"Baseball":3,"Basketball":2.5,"Hockey":2.5,"Football":3}.get(sport, 2)
            if exp_dt:
                from datetime import timedelta
                kickoff_dt = exp_dt - timedelta(hours=hours)

        display_dt = fmt_date(kickoff_dt) if kickoff_dt else ""
        outcomes = []
        for mk in mkts[:4]:   # limit to 4 for speed
            label = str(mk.get("yes_sub_title") or "").strip() or str(mk.get("ticker","")).split("-")[-1]
            try:
                yf = float(mk.get("yes_bid_dollars") or (mk.get("yes_bid") or 0)/100)
                nf = float(mk.get("no_bid_dollars") or (mk.get("no_bid") or 0)/100)
                outcomes.append((label[:32], f"{int(round(yf*100))}%", f"{int(round(yf*100))}¢", f"{int(round(nf*100))}¢"))
            except:
                outcomes.append((label[:32], "—", "—", "—"))
        return game_date, kickoff_dt, display_dt, outcomes

    processed = df.apply(extract, axis=1, result_type="expand")
    df = df.copy()
    df[["_game_date", "_kickoff_dt", "_display_dt", "_outcomes"]] = processed
    return df

# ====================== TITLE & CONTROLS ======================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([3, 1.4, 1])
with c1:
    search = st.text_input("", placeholder="🔍  Search team, player, market…", label_visibility="collapsed")
with c2:
    sort_by = st.selectbox("", ["Earliest first","Latest first","Default"], index=0, label_visibility="collapsed")
with c3:
    if st.button("Refresh", use_container_width=True):
        fetch_all.clear()
        process_markets.clear()
        st.rerun()

date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")
include_no_date = st.toggle("Include undated", value=True)

# ====================== LOAD DATA ======================
with st.spinner("Loading Kalshi markets..."):
    raw_df = fetch_all()
    if raw_df.empty:
        st.error("No data from Kalshi.")
        st.stop()

    raw_df["_series"] = raw_df.get("series_ticker", "").fillna("").str.upper()
    raw_df["_sport"] = raw_df["_series"].map(get_sport)
    raw_df["_is_sport"] = raw_df["_sport"] != ""

    df = process_markets(raw_df)

# ====================== YOUR ORIGINAL RENDER CARDS FUNCTION ======================
def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return
    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker = str(row.get("event_ticker","")).upper()
            cat = str(row.get("category","Other"))
            title = str(row.get("title",""))[:90]
            sport = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label = sport[:16] if sport else cat[:16]
            dt = str(row.get("_display_dt","Open"))
            outcomes = row.get("_outcomes") or []

            series_lower = str(row.get("series_ticker","")).lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker.lower()}" if series_lower else ""

            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</
