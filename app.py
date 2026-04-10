import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import tempfile

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== CSS (keep your full CSS unchanged) ======================
st.markdown("""
<style>
/* ── Your entire original CSS goes here (unchanged) ── */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
/* ... paste ALL your <style> content exactly as it was ... */
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ====================== CATEGORY METADATA (unchanged) ======================
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = { ... }   # ← Keep your original CAT_META dictionary

CAT_TAGS = { ... }   # ← Keep your original CAT_TAGS

SPORT_ICONS = { ... }  # ← Keep your original SPORT_ICONS

# ====================== BUILD SERIES_SPORT (THIS WAS MISSING) ======================
_SPORT_SERIES = { ... }   # ← **Paste your entire huge _SPORT_SERIES dictionary here** from the original file

# Build the lookup dictionary (this fixes the NameError)
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# ====================== SOCCER_COMP & SPORT_SUBTABS (keep as original) ======================
SOCCER_COMP = { ... }        # ← Paste your full SOCCER_COMP dict
SPORT_SUBTABS = { ... }      # ← Paste your full SPORT_SUBTABS dict

# ====================== HELPERS ======================
def safe_dt(val):
    try:
        if not val: return None
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().astimezone(UTC) if not pd.isna(ts) else None
    except:
        return None

def parse_game_date_from_ticker(event_ticker: str):
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

# ====================== KALSHI CLIENT ======================
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

# ====================== FETCH DATA (Optimized) ======================
@st.cache_data(ttl=900, show_spinner="Fetching markets from Kalshi...")
def fetch_all(max_pages: int = 25):
    events = []
    cursor = None

    for i in range(max_pages):
        try:
            resp = client.get_events(
                limit=200,
                status="open",
                with_nested_markets=True,
                cursor=cursor
            ).to_dict()

            batch = resp.get("events", [])
            if not batch:
                break

            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor:
                break

            time.sleep(0.04)
        except Exception as e:
            if "429" in str(e):
                time.sleep(2.5)
            else:
                break

    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"] = df["_series"].map(get_sport)          # ← Faster than .apply + lambda
    df["_is_sport"] = df["_sport"] != ""

    df["markets"] = df.get("markets", [[]] * len(df)).apply(lambda x: x if isinstance(x, list) else [])

    return df

# ====================== PROCESS MARKETS (Cached) ======================
@st.cache_data(ttl=900)
def process_markets(df: pd.DataFrame):
    if df.empty:
        return df.copy()

    def extract_row(row):
        mkts = row.get("markets", [])
        if not mkts:
            return None, None, None, "", []

        first = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport = row.get("_sport", "")

        game_date = parse_game_date_from_ticker(event_ticker)
        exp_dt = safe_dt(first.get("expected_expiration_time"))

        # Kickoff estimate
        kickoff_dt = None
        if game_date and sport:
            hours = {"Soccer": 2, "Baseball": 3, "Basketball": 2.5, "Hockey": 2.5, "Football": 3}.get(sport, 2)
            if exp_dt:
                from datetime import timedelta
                kickoff_dt = exp_dt - timedelta(hours=hours)

        display_dt = fmt_date(kickoff_dt) if kickoff_dt else ""
        sort_dt = game_date or (safe_dt(first.get("close_time")).date() if safe_dt(first.get("close_time")) else None)

        # Outcomes (limit to 5)
        outcomes = []
        for mk in mkts[:5]:
            label = str(mk.get("yes_sub_title") or "").strip() or str(mk.get("ticker","")).split("-")[-1]
            try:
                yf = float(mk.get("yes_bid_dollars") or (mk.get("yes_bid") or 0)/100)
                nf = float(mk.get("no_bid_dollars") or (mk.get("no_bid") or 0)/100)
                outcomes.append((label[:35], f"{int(round(yf*100))}%", f"{int(round(yf*100))}¢", f"{int(round(nf*100))}¢"))
            except:
                outcomes.append((label[:35], "—", "—", "—"))

        return sort_dt, game_date, kickoff_dt, display_dt, outcomes

    processed = df.apply(extract_row, axis=1, result_type="expand")
    df = df.copy()
    df[["_sort_dt", "_game_date", "_kickoff_dt", "_display_dt", "_outcomes"]] = processed
    return df

# ====================== MAIN APP ======================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

# Controls
c1, c2, c3 = st.columns([3, 1.4, 1])
with c1:
    search = st.text_input("", placeholder="🔍 Search team, player, market…", label_visibility="collapsed")
with c2:
    sort_by = st.selectbox("", ["Earliest first", "Latest first", "Default"], index=0, label_visibility="collapsed")
with c3:
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_all.clear()
        process_markets.clear()
        st.rerun()

# Date filter (simplified)
date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed", key="date_mode")
include_no_date = st.toggle("Include undated", value=True)

with st.spinner("Loading markets..."):
    raw_df = fetch_all()
    df = process_markets(raw_df)

if df.empty:
    st.error("No data received from Kalshi.")
    st.stop()

# Filtering logic (same as before, but cleaner)
filtered = df.copy()

# ... (keep your date filtering, search, and sorting logic here) ...

# Render function (keep your beautiful render_cards exactly as you had it)

# Navigation and tabs (keep your existing Sports sidebar + tab logic)

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 15 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
