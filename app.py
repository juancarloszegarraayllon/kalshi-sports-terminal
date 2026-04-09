import streamlit as st
import tempfile
import time
import json
import pandas as pd
import requests

st.set_page_config(page_title="Kalshi Structure Debug", layout="wide")
st.title("🔍 Kalshi Structure Debug — Export")

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

BASE = "https://api.elections.kalshi.com/trade-api/v2"

@st.cache_data(ttl=300)
def fetch_all_series():
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
            st.error(f"Error: {e}"); break
    return all_series

@st.cache_data(ttl=300)
def fetch_live_events():
    all_ev, cursor = [], None
    for _ in range(20):
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
            st.warning(f"Stopped at page: {e}"); break
    return all_ev

@st.cache_data(ttl=300)
def fetch_sport_filters():
    try:
        r = requests.get(f"{BASE}/search/filters_by_sport", timeout=10)
        return r.json()
    except Exception:
        return {}

with st.spinner("Fetching all data…"):
    all_series   = fetch_all_series()
    live_events  = fetch_live_events()
    sport_filter = fetch_sport_filters()

st.write(f"Series: **{len(all_series)}** | Live events: **{len(live_events)}**")

# ── Build full structure report ────────────────────────────────────────────────
def build_report():
    lines = []

    # 1. Series by category
    df_s = pd.DataFrame(all_series)
    lines.append("=" * 60)
    lines.append("SECTION 1: ALL SERIES BY CATEGORY")
    lines.append("=" * 60)

    for cat in sorted(df_s["category"].fillna("(none)").unique()):
        cat_df = df_s[df_s["category"].fillna("(none)") == cat]
        lines.append(f"\n### CATEGORY: {cat} ({len(cat_df)} series)")

        # Collect tags
        all_tags = []
        for tags in cat_df["tags"].dropna():
            if isinstance(tags, list): all_tags.extend(tags)
        lines.append(f"  Tags: {sorted(set(all_tags))}")

        # List series
        for _, row in cat_df.iterrows():
            tags = row.get("tags") or []
            lines.append(f"  - {row['ticker']} | {row.get('title','')} | tags: {tags}")

    # 2. Sport filters (competitions per sport)
    lines.append("\n" + "=" * 60)
    lines.append("SECTION 2: SPORT FILTERS (competitions per sport)")
    lines.append("=" * 60)
    filters = sport_filter.get("filters_by_sports", {})
    ordering = sport_filter.get("sport_ordering", list(filters.keys()))
    for sport in ordering:
        comps = list(filters.get(sport, {}).get("competitions", {}).keys())
        lines.append(f"\n### {sport}")
        lines.append(f"  Competitions: {comps}")

    # 3. Live events by category → series_ticker
    lines.append("\n" + "=" * 60)
    lines.append("SECTION 3: LIVE EVENTS BY CATEGORY → SERIES TICKER")
    lines.append("=" * 60)

    ev_df = pd.DataFrame(live_events)
    if "category" in ev_df.columns and "series_ticker" in ev_df.columns:
        for cat in sorted(ev_df["category"].fillna("(none)").unique()):
            cat_ev = ev_df[ev_df["category"].fillna("(none)") == cat]
            series_list = sorted(cat_ev["series_ticker"].dropna().unique().tolist())
            lines.append(f"\n### {cat} ({len(cat_ev)} events, {len(series_list)} unique series)")
            lines.append(f"  Series tickers: {series_list}")
            for _, row in cat_ev.iterrows():
                lines.append(f"  - {row.get('event_ticker','')} | series: {row.get('series_ticker','')} | {row.get('title','')[:80]}")

    # 4. Sports series with tags → which have live events
    lines.append("\n" + "=" * 60)
    lines.append("SECTION 4: SPORTS SERIES TAGS → LIVE EVENT SERIES TICKERS")
    lines.append("=" * 60)

    sports_series = df_s[df_s["category"] == "Sports"]
    live_series   = set(ev_df["series_ticker"].dropna().unique()) if "series_ticker" in ev_df.columns else set()

    tag_map = {}
    for _, row in sports_series.iterrows():
        tags = row.get("tags") or ["(no tag)"]
        if not isinstance(tags, list): tags = ["(no tag)"]
        for tag in tags:
            tag_map.setdefault(tag, []).append(row["ticker"])

    for tag, tickers in sorted(tag_map.items()):
        live = [t for t in tickers if t in live_series]
        lines.append(f"\n### Sport Tag: {tag}")
        lines.append(f"  All series ({len(tickers)}): {tickers}")
        lines.append(f"  Live now   ({len(live)}):  {live}")

    return "\n".join(lines)

# ── Generate and show download button ─────────────────────────────────────────
st.header("📥 Download Full Structure Report")
st.caption("Click the button below to download a text file with the complete category/series/event hierarchy")

report = build_report()

st.download_button(
    label     = "⬇️ Download structure report (.txt)",
    data      = report,
    file_name = "kalshi_structure.txt",
    mime      = "text/plain",
)

# Also show a preview
st.header("Preview")
st.text_area("Full report (scroll to read)", report, height=600)
