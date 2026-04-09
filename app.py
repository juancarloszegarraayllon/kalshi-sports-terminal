import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

UTC = timezone.utc

# -------------------------
# UTIL FUNCTIONS
# -------------------------

def safe_date(val):
    try:
        if val is None or val == "":
            return None
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts):
            return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except:
        return None

def fmt_date(d):
    try:
        return d.strftime("%b %d") if d else "Open"
    except:
        return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f <= 1 else int(round(f))}%"
    except:
        return "—"

# -------------------------
# API CLIENT
# -------------------------

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

# -------------------------
# SAFE PAGINATION (FIXED)
# -------------------------

def paginate(max_pages=20, with_markets=True):
    events = []
    cursor = None

    for _ in range(max_pages):
        for attempt in range(3):
            try:
                params = {"limit": 200, "status": "open"}
                if with_markets:
                    params["with_nested_markets"] = True
                if cursor:
                    params["cursor"] = cursor

                resp_raw = client.get_events(**params)

                try:
                    resp = resp_raw.to_dict()
                except:
                    resp = resp_raw if isinstance(resp_raw, dict) else {}

                batch = resp.get("events", [])
                if not batch:
                    return events

                events.extend(batch)
                cursor = resp.get("cursor") or resp.get("next_cursor")

                if not cursor:
                    return events

                time.sleep(0.2)
                break

            except Exception as e:
                if "429" in str(e):
                    time.sleep(2 + attempt)
                else:
                    return events

    return events

# -------------------------
# DATA FETCH (OPTIMIZED)
# -------------------------

@st.cache_data(ttl=600)
def fetch_data():
    raw = paginate()

    if not raw:
        return pd.DataFrame()

    df = pd.json_normalize(raw)

    # Ensure columns exist
    df["title"] = df.get("title", "").astype(str)
    df["category"] = df.get("category", "Other").astype(str)

    # Extract odds safely
    def extract(row):
        mkts = row.get("markets", [])

        if not isinstance(mkts, list) or not mkts:
            return "—", "—", None

        m = mkts[0] if isinstance(mkts[0], dict) else {}

        yes_val = m.get("yes_bid_dollars") or m.get("yes_bid") or m.get("yes_ask")
        no_val  = m.get("no_bid_dollars")  or m.get("no_bid")  or m.get("no_ask")

        yes = fmt_pct(yes_val)
        no  = fmt_pct(no_val)

        close = None
        for mk in mkts:
            if not isinstance(mk, dict):
                continue
            d = safe_date(mk.get("close_time"))
            if d and (close is None or d < close):
                close = d

        return yes, no, close

    info = df.apply(extract, axis=1, result_type="expand")

    df["_yes"] = info[0]
    df["_no"] = info[1]
    df["_date"] = info[2]

    df["_display_date"] = df["_date"].apply(fmt_date)

    return df

# -------------------------
# SIDEBAR
# -------------------------

with st.sidebar:
    st.title("📡 Kalshi Terminal")

    search = st.text_input("Search")

    debug = st.checkbox("🧪 Debug mode")

    if st.button("🔄 Refresh"):
        fetch_data.clear()
        st.rerun()

# -------------------------
# MAIN
# -------------------------

st.title("📡 Kalshi Markets Terminal")

with st.spinner("Loading markets..."):
    df = fetch_data()

if df.empty:
    st.error("No data loaded")
    st.stop()

# Search filter
if search:
    s = search.lower()
    df = df[
        df["title"].str.lower().str.contains(s, na=False) |
        df["category"].str.lower().str.contains(s, na=False)
    ]

# Metrics
st.metric("Total Markets", len(df))

# Debug
if debug:
    st.write(df.head())
    st.write(df.columns)

# -------------------------
# RENDER CARDS
# -------------------------

cols = st.columns(3)

for i, row in df.iterrows():
    col = cols[i % 3]

    with col:
        st.markdown(f"""
        <div style="padding:15px;border:1px solid #222;border-radius:10px;margin-bottom:10px">
            <div style="font-size:12px;color:gray">{row['_display_date']}</div>
            <div style="font-size:16px;margin:8px 0">{row['title']}</div>
            <div style="display:flex;gap:10px">
                <div style="color:#4ade80">YES {row['_yes']}</div>
                <div style="color:#f87171">NO {row['_no']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
