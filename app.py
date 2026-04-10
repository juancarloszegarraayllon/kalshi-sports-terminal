import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta

st.set_page_config(page_title="OddsIQ", layout="wide")

# -----------------------------
# FAST API FETCH (NO MARKETS)
# -----------------------------
@st.cache_data(ttl=600)
def fetch_events():
    from kalshi_python_sync import Configuration, KalshiClient

    key_id = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str)
        pem = f.name

    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem

    client = KalshiClient(cfg)

    events = []
    cursor = None

    for _ in range(5):  # LIMIT PAGES (FAST)
        resp = client.get_events(limit=200, status="open", cursor=cursor).to_dict()
        batch = resp.get("events", [])

        if not batch:
            break

        events.extend(batch)
        cursor = resp.get("cursor")

        if not cursor:
            break

    return pd.DataFrame(events)

# -----------------------------
# UI
# -----------------------------
st.title("OddsIQ ⚡")

search = st.text_input("Search")
fast_mode = st.toggle("⚡ Fast mode", value=True)

with st.spinner("Loading fast data..."):
    df = fetch_events()

if df.empty:
    st.error("No data")
    st.stop()

# -----------------------------
# FILTERING
# -----------------------------
filtered = df.copy()

if search:
    s = search.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(s, na=False)
    ]

# FAST MODE LIMIT
if fast_mode:
    filtered = filtered.head(150)

# -----------------------------
# PAGINATION
# -----------------------------
page_size = 50
page = st.number_input("Page", min_value=1, step=1, value=1)

start = (page - 1) * page_size
end = start + page_size

visible = filtered.iloc[start:end]

# -----------------------------
# RENDER
# -----------------------------
def render_cards(data):
    if data.empty:
        st.write("No results")
        return

    for _, row in data.iterrows():
        with st.container():
            st.markdown(f"**{row.get('title', 'No title')}**")
            st.caption(row.get("event_ticker", ""))
            st.divider()

render_cards(visible)

# -----------------------------
# OPTIONAL: LOAD MARKETS ON CLICK
# -----------------------------
@st.cache_data
def fetch_markets(event_ticker):
    from kalshi_python_sync import Configuration, KalshiClient

    key_id = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str)
        pem = f.name

    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem

    client = KalshiClient(cfg)

    return client.get_event(event_ticker=event_ticker, with_nested_markets=True).to_dict()

st.markdown("---")
st.subheader("Load market details")

selected = st.text_input("Enter event ticker to load markets")

if selected:
    with st.spinner("Loading markets..."):
        data = fetch_markets(selected)
        st.json(data)
