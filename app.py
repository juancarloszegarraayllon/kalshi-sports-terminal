import streamlit as st
import tempfile
import time
import pandas as pd

st.set_page_config(page_title="Kalshi Structure Debug", layout="wide")
st.title("🔍 Kalshi Full Structure Debug")
st.caption("This tool pulls the real category → series → events hierarchy live from the API.")

# ── Connect ────────────────────────────────────────────────────────────────────
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
st.success("✅ Connected")

# ── Step 1: Pull ALL series (paginated) ────────────────────────────────────────
st.header("Step 1 — All Series (category + tags)")

@st.cache_data(ttl=300)
def fetch_all_series():
    import requests
    BASE = "https://api.elections.kalshi.com/trade-api/v2"
    all_series, cursor = [], None
    for _ in range(60):
        try:
            params = {"limit": 200}
            if cursor: params["cursor"] = cursor
            r = requests.get(f"{BASE}/series", params=params, timeout=15)
            data = r.json()
            batch = data.get("series", [])
            if not batch: break
            all_series.extend(batch)
            cursor = data.get("cursor")
            if not cursor: break
            time.sleep(0.3)
        except Exception as e:
            st.error(f"Series fetch error: {e}"); break
    return all_series

with st.spinner("Fetching all series…"):
    all_series = fetch_all_series()

st.write(f"**Total series:** {len(all_series)}")

df_s = pd.DataFrame(all_series)
show_cols = [c for c in ["ticker","title","category","tags","frequency"] if c in df_s.columns]

# Category breakdown
st.subheader("Categories & counts:")
cat_counts = df_s["category"].fillna("(none)").value_counts()
st.dataframe(cat_counts.rename("series count").reset_index())

# For each category: list series tickers + tags
st.subheader("Category → Series Tickers → Tags:")
for cat in sorted(df_s["category"].fillna("(none)").unique()):
    cat_df = df_s[df_s["category"].fillna("(none)") == cat]
    with st.expander(f"📂 {cat}  ({len(cat_df)} series)"):
        # Show unique tags within this category
        all_tags = []
        for tags in cat_df["tags"].dropna():
            if isinstance(tags, list):
                all_tags.extend(tags)
        unique_tags = sorted(set(all_tags))
        st.write(f"**Tags (sub-categories):** {unique_tags}")
        st.dataframe(cat_df[show_cols].reset_index(drop=True))

# ── Step 2: For Sports — show tags as sub-categories ──────────────────────────
st.header("Step 2 — Sports Series: Tag → Series Tickers")

sports_df = df_s[df_s["category"] == "Sports"].copy()
st.write(f"**Sports series total:** {len(sports_df)}")

# Explode tags
sports_df["_tags"] = sports_df["tags"].apply(lambda x: x if isinstance(x, list) else ["(no tag)"])
tag_to_series = {}
for _, row in sports_df.iterrows():
    for tag in row["_tags"]:
        tag_to_series.setdefault(tag, []).append(row["ticker"])

st.subheader("Sport Tag → Series Tickers:")
for tag, tickers in sorted(tag_to_series.items()):
    with st.expander(f"🏷️ {tag}  ({len(tickers)} series)"):
        st.write(tickers)

# ── Step 3: Fetch sample events for each sport tag ────────────────────────────
st.header("Step 3 — Sample Events per Sport Tag")
st.caption("Fetches up to 5 events for each sport series ticker to confirm what's live")

if st.button("▶️ Run event samples (slow — ~2 min)"):
    tag_events = {}
    all_sport_tickers = sorted(sports_df["ticker"].unique().tolist())
    prog = st.progress(0)
    for i, ticker in enumerate(all_sport_tickers):
        prog.progress((i+1)/len(all_sport_tickers), text=f"Fetching {ticker}…")
        try:
            resp = client.get_events(limit=3, status="open", series_ticker=ticker)
            events = resp.to_dict().get("events", [])
            if events:
                tag_events[ticker] = events
        except Exception:
            pass
        time.sleep(0.2)
    prog.empty()

    st.write(f"Series with live events: {len(tag_events)} / {len(all_sport_tickers)}")

    # Group back by tag
    for tag, tickers in sorted(tag_to_series.items()):
        live = {t: tag_events[t] for t in tickers if t in tag_events}
        if not live: continue
        with st.expander(f"🏷️ {tag} — {len(live)} active series"):
            for ticker, events in live.items():
                st.write(f"**{ticker}**")
                for e in events:
                    st.write(f"  • {e.get('title')} | series: {e.get('series_ticker')} | cat: {e.get('category')}")

# ── Step 4: What series tickers appear in live open events? ───────────────────
st.header("Step 4 — Live Events: Series Ticker Breakdown")
st.caption("Pages through all open events and shows the unique series_tickers that appear")

@st.cache_data(ttl=300)
def fetch_live_events_sample():
    all_ev, cursor = [], None
    for _ in range(15):  # 15 pages = 3000 events
        try:
            kw = {"limit": 200, "status": "open"}
            if cursor: kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            all_ev.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.35)
        except Exception as e:
            st.warning(f"Stopped: {e}"); break
    return all_ev

with st.spinner("Fetching live events sample (up to 3000)…"):
    live_events = fetch_live_events_sample()

ev_df = pd.DataFrame(live_events)
st.write(f"**Live events fetched:** {len(ev_df)}")

if "series_ticker" in ev_df.columns and "category" in ev_df.columns:
    st.subheader("Category → unique series_tickers in live events:")
    for cat in sorted(ev_df["category"].fillna("(none)").unique()):
        cat_ev = ev_df[ev_df["category"].fillna("(none)") == cat]
        series = sorted(cat_ev["series_ticker"].dropna().unique().tolist())
        with st.expander(f"📂 {cat}  ({len(cat_ev)} events, {len(series)} series)"):
            st.write("**Series tickers:**", series)
            st.dataframe(
                cat_ev[["event_ticker","series_ticker","title"]].head(20).reset_index(drop=True)
            )
