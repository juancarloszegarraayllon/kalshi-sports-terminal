import streamlit as st
import pandas as pd
import tempfile
import time
import json

st.set_page_config(page_title="Kalshi Live Structure Debug", layout="wide")
st.title("🔍 Live Sports Structure Debug")

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

def paginate(category=None, max_pages=30):
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit": 200, "status": "open"}
            if category: kw["category"] = category
            if cursor:   kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.3)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

st.header("All Live Sports Events — series_ticker breakdown")

with st.spinner("Fetching all open events..."):
    all_events = paginate(max_pages=30)

df = pd.DataFrame(all_events)
df["series"] = df.get("series_ticker", pd.Series("", index=df.index)).fillna("")
df["cat"]    = df.get("category", pd.Series("", index=df.index)).fillna("")

sports_df = df[df["cat"] == "Sports"][["event_ticker","series","title","cat"]].copy()

st.write(f"Total events: {len(df)} | Sports category events: {len(sports_df)}")

st.subheader("All unique series_tickers in Sports category events")
series_counts = sports_df["series"].value_counts()
st.dataframe(series_counts.rename("event_count").reset_index().rename(columns={"index":"series_ticker"}))

st.subheader("Download: full sports event list with series_ticker")
csv = sports_df.to_csv(index=False)
st.download_button("⬇️ Download sports_events.csv", csv, "sports_events.csv", "text/csv")

st.subheader("All events grouped by series_ticker")
for series, group in sports_df.groupby("series"):
    with st.expander(f"📂 {series} ({len(group)} events)"):
        for _, row in group.iterrows():
            st.write(f"• {row['title'][:80]}")

st.header("All series_tickers across ALL categories")
series_by_cat = df.groupby("cat")["series"].apply(lambda x: sorted(x.dropna().unique().tolist()))
out = {}
for cat, series in series_by_cat.items():
    out[cat] = series
    with st.expander(f"📂 {cat} ({len(series)} unique series)"):
        st.write(series)

st.download_button(
    "⬇️ Download full series_ticker map (JSON)",
    json.dumps(out, indent=2),
    "series_map.json",
    "application/json"
)
