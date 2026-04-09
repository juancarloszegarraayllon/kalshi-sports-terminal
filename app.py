import streamlit as st
import tempfile
import requests
import pandas as pd
import time

st.set_page_config(page_title="Kalshi Series Debug", layout="wide")
st.title("🔍 Kalshi Sports Series Finder")

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

@st.cache_resource
def get_client():
    from kalshi_python_sync import Configuration, KalshiClient
    key_id  = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str); pem = f.name
    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem
    return KalshiClient(cfg)

client = get_client()

# ── Fetch series list via raw HTTP (no SDK limit issue) ────────────────────────
st.header("1. All Series with category=Sports")
st.caption("Fetches the series list and filters for Sports category")

@st.cache_data(ttl=300)
def fetch_all_series():
    all_series = []
    cursor = None
    for _ in range(20):
        try:
            url = f"{BASE_URL}/series"
            params = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            batch = data.get("series", [])
            if not batch:
                break
            all_series.extend(batch)
            cursor = data.get("cursor")
            if not cursor:
                break
            time.sleep(0.3)
        except Exception as e:
            st.error(f"Error: {e}")
            break
    return all_series

with st.spinner("Fetching all series..."):
    all_series = fetch_all_series()

st.write(f"Total series fetched: {len(all_series)}")

if all_series:
    df = pd.DataFrame(all_series)
    st.write("Columns:", list(df.columns))

    # Show sports series
    if "category" in df.columns:
        sports_df = df[df["category"] == "Sports"]
        st.write(f"Sports series: {len(sports_df)}")
        st.subheader("All Sports series:")
        show_cols = [c for c in ["ticker","title","category","tags","frequency"] if c in df.columns]
        st.dataframe(sports_df[show_cols])

        st.subheader("All unique categories:")
        st.write(sorted(df["category"].dropna().unique().tolist()))

        st.subheader("First 3 sports series (raw):")
        for s in sports_df.head(3).to_dict("records"):
            st.json(s)

# ── Fetch events for known sport series tickers ────────────────────────────────
st.header("2. Sample events for sport series tickers")
st.caption("Tests fetching events with specific series_ticker values")

SPORT_SERIES_TO_TEST = [
    "EPL", "KXEPL", "NBA", "KXNBA", "ATP", "KXATP",
    "MLB", "KXMLB", "NHL", "KXNHL", "MLS", "KXMLS",
    "IPL", "KXIPL", "UFC", "KXUFC", "F1", "KXF1",
    "LALIGA", "KXLALIGA", "UCL", "KXUCL",
]

results = {}
prog = st.progress(0)
for i, ticker in enumerate(SPORT_SERIES_TO_TEST):
    try:
        resp = client.get_events(limit=5, status="open", series_ticker=ticker)
        events = resp.to_dict().get("events", [])
        if events:
            results[ticker] = events[:2]
    except Exception:
        pass
    prog.progress((i+1)/len(SPORT_SERIES_TO_TEST))
prog.empty()

st.write(f"Series tickers that returned events: {list(results.keys())}")
for ticker, events in results.items():
    with st.expander(f"✅ {ticker} — {len(events)} events"):
        for e in events:
            st.write(f"**{e.get('title')}** | category: {e.get('category')} | series: {e.get('series_ticker')}")

# ── Fetch ALL open events and show series tickers ──────────────────────────────
st.header("3. All open events — unique series_ticker values by category")
st.caption("Paginates all events and shows what series tickers exist")

@st.cache_data(ttl=300)
def fetch_sample_events():
    all_events = []
    cursor = None
    for _ in range(5):  # just 5 pages = 1000 events for speed
        try:
            kw = {"limit": 200, "status": "open"}
            if cursor: kw["cursor"] = cursor
            resp = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            all_events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.35)
        except Exception as e:
            st.error(f"Fetch error: {e}")
            break
    return all_events

with st.spinner("Fetching events sample..."):
    events = fetch_sample_events()

edf = pd.DataFrame(events)
st.write(f"Events fetched: {len(edf)}")

if "series_ticker" in edf.columns and "category" in edf.columns:
    st.subheader("Series tickers for Sports category events:")
    sports_events = edf[edf["category"] == "Sports"]
    st.write(f"Sports events in sample: {len(sports_events)}")
    if not sports_events.empty:
        st.dataframe(sports_events[["event_ticker","series_ticker","title","category"]].head(50))
    
    st.subheader("ALL unique series_tickers across all categories:")
    series_by_cat = edf.groupby("category")["series_ticker"].apply(lambda x: sorted(x.dropna().unique().tolist()))
    for cat, series in series_by_cat.items():
        with st.expander(f"📂 {cat} — {len(series)} series"):
            st.write(series)
