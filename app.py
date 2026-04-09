import streamlit as st
import tempfile
import requests
import pandas as pd

st.set_page_config(page_title="Kalshi Debug", layout="wide")
st.title("🔍 Kalshi Category & Tag Structure Debug")

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

# ── 1. Tags by categories ──────────────────────────────────────────────────────
st.header("1. Tags by Categories")
st.caption("GET /search/tags_by_categories — top-level categories mapped to their tags")
try:
    r = requests.get(f"{BASE_URL}/search/tags_by_categories")
    data = r.json()
    tags_by_cat = data.get("tags_by_categories", {})
    if tags_by_cat:
        for cat, tags in tags_by_cat.items():
            with st.expander(f"📂 {cat} ({len(tags)} tags)"):
                st.write(tags)
    else:
        st.warning("Empty response — showing raw:")
        st.json(data)
except Exception as e:
    st.error(f"Error: {e}")

# ── 2. Sport filters ───────────────────────────────────────────────────────────
st.header("2. Sport Filters")
st.caption("GET /search/filters_by_sport — sports with their scopes and competitions")
try:
    r = requests.get(f"{BASE_URL}/search/filters_by_sport")
    data = r.json()
    filters = data.get("filters_by_sports", {})
    ordering = data.get("sport_ordering", [])
    st.write("**Sport ordering:**", ordering)
    for sport in ordering:
        details = filters.get(sport, {})
        with st.expander(f"🏟️ {sport}"):
            st.json(details)
except Exception as e:
    st.error(f"Error: {e}")

# ── 3. Series list ─────────────────────────────────────────────────────────────
st.header("3. Series List — Category + Tags per Series")
st.caption("Each series has a category and tags array — this reveals the real sub-category structure")
try:
    resp = client.get_series_list(limit=200)
    series_list = resp.to_dict().get("series", [])
    st.write(f"Total series: {len(series_list)}")

    if series_list:
        df = pd.DataFrame(series_list)
        st.write("**Columns:**", list(df.columns))

        # Category → tags mapping
        cat_tags = {}
        for s in series_list:
            cat  = s.get("category", "?")
            tags = s.get("tags") or []
            cat_tags.setdefault(cat, set()).update(tags)

        st.subheader("Category → Sub-tags:")
        for cat in sorted(cat_tags.keys()):
            tags = sorted(cat_tags[cat])
            with st.expander(f"📂 {cat} — {len(tags)} tags"):
                st.write(tags)

        st.subheader("First 5 series (raw):")
        for s in series_list[:5]:
            st.json(s)
except Exception as e:
    st.error(f"Series list error: {e}")

# ── 4. Events — category + series + sub_title ─────────────────────────────────
st.header("4. Events — Category + Series Ticker + Sub Title")
st.caption("Shows the real event hierarchy: category → series_ticker → sub_title")
try:
    resp = client.get_events(limit=200, status="open")
    events = resp.to_dict().get("events", [])
    st.write(f"Events fetched: {len(events)}")
    df = pd.DataFrame(events)

    st.subheader("All columns:")
    st.write(list(df.columns))

    st.subheader("Category counts:")
    st.dataframe(df["category"].value_counts().rename("count").reset_index())

    if "series_ticker" in df.columns:
        df["_prefix"] = df["series_ticker"].str.split("-").str[0]
        st.subheader("Series ticker prefixes by category:")
        for cat in sorted(df["category"].unique()):
            prefixes = sorted(df[df["category"] == cat]["_prefix"].dropna().unique().tolist())
            with st.expander(f"📂 {cat} — {len(prefixes)} series"):
                st.write(prefixes)

    show_cols = [c for c in ["event_ticker","series_ticker","category","title","sub_title","strike_period"] if c in df.columns]
    st.subheader("Sample events (first 30):")
    st.dataframe(df[show_cols].head(30))

except Exception as e:
    st.error(f"Events error: {e}")
