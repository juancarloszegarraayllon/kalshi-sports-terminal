import streamlit as st
import pandas as pd
import tempfile
from datetime import date, timedelta

st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏟️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
.stApp { background: #0a0a0f; }
section[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e32; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #6b7280 !important; font-size: 11px !important; letter-spacing: .08em; text-transform: uppercase; }
h1 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; color: #f0f0ff !important; letter-spacing: -.02em; font-size: 2.2rem !important; }
.metric-strip { display: flex; gap: 12px; margin-bottom: 28px; flex-wrap: wrap; }
.metric-box { background: #0f0f1a; border: 1px solid #1e1e32; border-radius: 10px; padding: 14px 20px; flex: 1; min-width: 120px; }
.metric-label { font-size: 10px; color: #4b5563; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 500; color: #a5b4fc; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.market-card { background: #0f0f1a; border: 1px solid #1e1e32; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; transition: border-color .2s, transform .15s; }
.market-card:hover { border-color: #4f46e5; transform: translateY(-2px); }
.market-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #4f46e5, #818cf8); opacity: 0; transition: opacity .2s; }
.market-card:hover::before { opacity: 1; }
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.sport-pill { font-size: 10px; font-weight: 500; letter-spacing: .1em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; background: #1e1e32; color: #818cf8; border: 1px solid #2d2d55; }
.date-text { font-size: 11px; color: #374151; }
.card-title { font-size: 15px; font-weight: 500; color: #e2e8f0; line-height: 1.45; margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-icon { font-size: 22px; margin-bottom: 8px; display: block; }
.card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1a1a2e; padding-top: 10px; }
.ticker-text { font-size: 10px; color: #374151; letter-spacing: .06em; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.empty-state { text-align: center; padding: 80px 20px; color: #374151; font-size: 14px; letter-spacing: .05em; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
hr { border-color: #1e1e32 !important; }
</style>
""", unsafe_allow_html=True)

# ── API connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        api_key_id = st.secrets["KALSHI_API_KEY_ID"]
        private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(private_key_str)
            pem_path = f.name
        cfg = Configuration()
        cfg.api_key_id = api_key_id
        cfg.private_key_pem_path = pem_path
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"❌ API connection failed: {e}")
        st.stop()

client = get_client()

# ── Fetch sports events ────────────────────────────────────────────────────────
@st.cache_data(ttl=180)
def fetch_sports():
    all_events = []
    seen = set()
    debug_info = {}

    # Strategy 1: category="Sports"
    try:
        resp = client.get_events(limit=200, status="open", category="Sports")
        events = resp.to_dict().get("events", [])
        debug_info["category=Sports"] = len(events)
        for e in events:
            t = e.get("event_ticker")
            if t not in seen:
                e["_source"] = "category=Sports"
                all_events.append(e)
                seen.add(t)
    except Exception as ex:
        debug_info["category=Sports error"] = str(ex)

    # Strategy 2: known sports series tickers
    SPORT_SERIES = [
        "KXNBA", "KXMLB", "KXNHL", "KXNFL", "KXNCAAB", "KXNCAAF",
        "KXMLS", "KXPGA", "KXATP", "KXWTA", "KXUFC", "KXF1",
        "NBA", "MLB", "NHL", "NFL",
    ]
    series_found = 0
    for series in SPORT_SERIES:
        try:
            resp = client.get_events(limit=100, status="open", series_ticker=series)
            events = resp.to_dict().get("events", [])
            for e in events:
                t = e.get("event_ticker")
                if t not in seen:
                    e["_source"] = f"series={series}"
                    all_events.append(e)
                    seen.add(t)
                    series_found += 1
        except Exception:
            pass
    debug_info["series_ticker hits"] = series_found

    # Strategy 3: get_markets with category=Sports
    if not all_events:
        try:
            resp = client.get_markets(limit=200, status="open", category="Sports")
            markets = resp.to_dict().get("markets", [])
            debug_info["markets endpoint"] = len(markets)
            for m in markets:
                t = m.get("ticker", m.get("event_ticker", ""))
                if t not in seen:
                    m["event_ticker"] = t
                    m["title"] = m.get("title", m.get("subtitle", ""))
                    m["_source"] = "markets"
                    all_events.append(m)
                    seen.add(t)
        except Exception as ex:
            debug_info["markets error"] = str(ex)

    # Strategy 4: scan all events for sports category
    if not all_events:
        try:
            resp = client.get_events(limit=200, status="open")
            events = resp.to_dict().get("events", [])
            sports = [e for e in events if str(e.get("category","")).lower() == "sports"]
            debug_info["scan all for Sports category"] = len(sports)
            for e in sports:
                t = e.get("event_ticker")
                if t not in seen:
                    e["_source"] = "full scan"
                    all_events.append(e)
                    seen.add(t)
        except Exception as ex:
            debug_info["scan error"] = str(ex)

    if not all_events:
        return pd.DataFrame(), debug_info

    df = pd.DataFrame(all_events)

    # Parse dates
    for col in ["strike_date", "end_date", "close_time", "expiration_time"]:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
            if parsed.notna().any():
                df["_parsed_date"] = parsed
                break
    if "_parsed_date" not in df.columns:
        df["_parsed_date"] = pd.NaT

    return df, debug_info


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏟️ Filters")
    search = st.text_input("Search", placeholder="team, market, keyword…")
    days_ahead = st.slider("Days ahead", 0, 60, 30)
    st.markdown("---")
    show_debug = st.checkbox("Debug mode")
    if st.button("🔄 Refresh"):
        fetch_sports.clear()
        st.rerun()

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("🏟️ Kalshi Sports Terminal")

with st.spinner("Fetching sports markets…"):
    df, debug_info = fetch_sports()

# ── Debug ──────────────────────────────────────────────────────────────────────
if show_debug:
    with st.expander("🔍 Debug info", expanded=True):
        st.write("**Fetch strategy results:**", debug_info)
        st.write(f"**Total rows:** {len(df)}")
        if not df.empty:
            st.write("**Columns:**", list(df.columns))
            if "_source" in df.columns:
                st.write("**Sources:**", df["_source"].value_counts().to_dict())
            cols = [c for c in ["event_ticker","category","title","_source"] if c in df.columns]
            st.dataframe(df[cols].head(30))

if df.empty:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📡</div>
        No sports markets found from any strategy.<br><br>
        Enable <b>Debug mode</b> in the sidebar to see what the API returned.<br>
        Kalshi may not have active sports markets right now, or the category name differs.
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Filter ─────────────────────────────────────────────────────────────────────
filtered = df.copy()

today = date.today()
end   = today + timedelta(days=days_ahead)

def in_window(d):
    if pd.isna(d): return True
    try:
        return today <= d.tz_convert("US/Eastern").date() <= end
    except Exception:
        return True

if "_parsed_date" in filtered.columns:
    filtered = filtered[filtered["_parsed_date"].apply(in_window)]

if search:
    title_match  = filtered.get("title", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
    ticker_match = filtered.get("event_ticker", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
    filtered = filtered[title_match | ticker_match]

if "event_ticker" in filtered.columns:
    filtered = filtered.drop_duplicates(subset=["event_ticker"])

# ── Metrics ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Sport markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
  <div class="metric-box"><div class="metric-label">Window</div><div class="metric-value">+{days_ahead}d</div></div>
</div>
""", unsafe_allow_html=True)

# ── Cards ──────────────────────────────────────────────────────────────────────
def get_icon(ticker):
    t = ticker.upper()
    if "NBA" in t:  return "🏀"
    if "MLB" in t:  return "⚾"
    if "NHL" in t:  return "🏒"
    if "NFL" in t:  return "🏈"
    if "GOLF" in t or "PGA" in t: return "⛳"
    if "TEN" in t or "ATP" in t or "WTA" in t: return "🎾"
    if "SOC" in t or "MLS" in t or "EPL" in t: return "⚽"
    if "UFC" in t or "MMA" in t: return "🥊"
    if "NCAAB" in t: return "🏀"
    if "NCAAF" in t: return "🏈"
    if "F1" in t or "NASCAR" in t: return "🏎️"
    return "🏟️"

def get_label(ticker):
    t = ticker.upper()
    for league in ["NBA","MLB","NHL","NFL","PGA","ATP","WTA","MLS","EPL","NCAAB","NCAAF","UFC","F1","NASCAR"]:
        if league in t: return league
    return "SPORT"

if filtered.empty:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">🔍</div>
        No events match your filters.<br>Try widening the date range or clearing the search.
    </div>""", unsafe_allow_html=True)
else:
    cards_html = '<div class="card-grid">'
    for _, row in filtered.iterrows():
        try:
            ticker    = str(row.get("event_ticker", "")).upper()
            title_raw = str(row.get("title", "Unknown"))
            title     = title_raw.split(":")[-1].replace("Will the ", "").split("?")[0].strip() or title_raw[:80]
            icon      = get_icon(ticker)
            label     = get_label(ticker)
            d         = row.get("_parsed_date")
            try:
                display_date = pd.Timestamp(d).tz_convert("US/Eastern").strftime("%b %d") if pd.notna(d) else "Open"
            except Exception:
                display_date = "Open"

            cards_html += f"""
            <div class="market-card">
                <div class="card-top">
                    <span class="sport-pill">{label}</span>
                    <span class="date-text">{display_date}</span>
                </div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">
                    <span class="ticker-text">{ticker}</span>
                    <span class="status-dot"></span>
                </div>
            </div>"""
        except Exception:
            continue
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI SPORTS TERMINAL · REFRESHES EVERY 3 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
