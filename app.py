import streamlit as st
import pandas as pd
import tempfile
from datetime import date, timedelta

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏟️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.stApp { background: #0a0a0f; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e32;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] p { color: #6b7280 !important; font-size: 11px !important; letter-spacing: .08em; text-transform: uppercase; }
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] .stTextInput input {
    background: #1a1a2e !important; border: 1px solid #2d2d4a !important;
    color: #e2e8f0 !important; border-radius: 6px !important;
}

/* Title */
h1 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important;
     color: #f0f0ff !important; letter-spacing: -.02em; font-size: 2.2rem !important; }

/* Metric strip */
.metric-strip {
    display: flex; gap: 12px; margin-bottom: 28px; flex-wrap: wrap;
}
.metric-box {
    background: #0f0f1a; border: 1px solid #1e1e32; border-radius: 10px;
    padding: 14px 20px; flex: 1; min-width: 120px;
}
.metric-label { font-size: 10px; color: #4b5563; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 500; color: #a5b4fc; }

/* Cards */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.market-card {
    background: #0f0f1a;
    border: 1px solid #1e1e32;
    border-radius: 12px;
    padding: 18px 20px;
    transition: border-color .2s, transform .15s;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}
.market-card:hover { border-color: #4f46e5; transform: translateY(-2px); }
.market-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #4f46e5, #818cf8);
    opacity: 0; transition: opacity .2s;
}
.market-card:hover::before { opacity: 1; }

.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.sport-pill {
    font-size: 10px; font-weight: 500; letter-spacing: .1em; text-transform: uppercase;
    padding: 3px 10px; border-radius: 4px;
    background: #1e1e32; color: #818cf8; border: 1px solid #2d2d55;
}
.date-text { font-size: 11px; color: #374151; }

.card-title {
    font-size: 15px; font-weight: 500; color: #e2e8f0;
    line-height: 1.45; margin-bottom: 14px;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.card-icon { font-size: 22px; margin-bottom: 8px; display: block; }

.card-footer {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid #1a1a2e; padding-top: 10px; margin-top: auto;
}
.ticker-text { font-size: 10px; color: #374151; letter-spacing: .06em; }
.status-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #22c55e;
    box-shadow: 0 0 6px #22c55e;
}

/* No results */
.empty-state {
    text-align: center; padding: 80px 20px;
    color: #374151; font-size: 14px; letter-spacing: .05em;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }

/* Debug table */
.stDataFrame { background: #0f0f1a !important; }

/* Divider */
hr { border-color: #1e1e32 !important; }
</style>
""", unsafe_allow_html=True)

# ── API connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        api_key_id     = st.secrets["KALSHI_API_KEY_ID"]
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

# ── Data fetch — NO pre-filtering, get everything then let user filter ─────────
@st.cache_data(ttl=180)
def fetch_all_events():
    """Fetch all open events from Kalshi without pre-filtering."""
    try:
        response = client.get_events(limit=200, status="open")
        events   = response.to_dict().get("events", [])
        if not events:
            return pd.DataFrame()

        df = pd.DataFrame(events)

        # ── Parse dates from whichever field exists ────────────────────────────
        for col in ["strike_date", "end_date", "close_time", "expiration_time", "created_time"]:
            if col in df.columns:
                df["_parsed_date"] = pd.to_datetime(df[col], errors="coerce", utc=True)
                filled = df["_parsed_date"].notna().sum()
                if filled > 0:
                    break   # use the first column that gives real dates

        if "_parsed_date" not in df.columns:
            df["_parsed_date"] = pd.NaT

        # ── Sport detection heuristic ─────────────────────────────────────────
        SPORT_TOKENS = [
            "NBA","MLB","NHL","NFL","NCAAB","NCAAF","NCAAW",
            "MLS","EPL","UEFA","FIFA","PGA","GOLF","ATP","WTA",
            "TEN","SOC","KX","SPORT","BRACKET","PLAYOFF",
            "CHAMPIONSHIP","SUPERBOWL","WORLDSERIES","STANLEYCUP",
        ]
        SPORT_TITLE_WORDS = [
            "Warriors","Lakers","Celtics","Knicks","Nets","Heat","Bucks","Suns",
            "Nuggets","Clippers","Mavericks","Grizzlies","76ers","Hawks",
            "Yankees","Dodgers","Red Sox","Cubs","Astros","Mets","Braves",
            "Chiefs","Cowboys","Eagles","Patriots","Bills","49ers","Packers",
            "Maple Leafs","Bruins","Rangers","Lightning","Avalanche","Oilers",
            "Soccer","Football","Basketball","Baseball","Hockey","Tennis","Golf",
            "World Cup","Super Bowl","Stanley Cup","March Madness","playoff",
            "championship","bracket","pennant","series",
        ]

        def is_sport(row):
            ticker = str(row.get("event_ticker","")).upper()
            cat    = str(row.get("category","")).upper()
            title  = str(row.get("title",""))
            # 1. ticker prefix match
            if any(tok in ticker for tok in SPORT_TOKENS):
                return True
            # 2. category field
            if "SPORT" in cat:
                return True
            # 3. title keyword
            if any(w.lower() in title.lower() for w in SPORT_TITLE_WORDS):
                return True
            return False

        df["_is_sport"] = df.apply(is_sport, axis=1)
        return df

    except Exception as e:
        st.error(f"Fetch error: {e}")
        return pd.DataFrame()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏟️ Filters")

    show_only_sports = st.toggle("Sports events only", value=True)
    search = st.text_input("Search", placeholder="team, market, keyword…")

    st.markdown("---")
    st.markdown("**Date window**")
    days_ahead = st.slider("Days ahead", 0, 30, 14)

    st.markdown("---")
    show_debug = st.checkbox("Debug mode")
    if st.button("🔄 Refresh data"):
        fetch_all_events.clear()
        st.rerun()

# ── Load + filter ──────────────────────────────────────────────────────────────
with st.spinner("Loading markets…"):
    df = fetch_all_events()

st.title("🏟️ Kalshi Sports Terminal")

if df.empty:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📡</div>
        No data returned from the API.<br>Check your credentials in st.secrets.
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Debug view ─────────────────────────────────────────────────────────────────
if show_debug:
    with st.expander("🔍 Raw API data", expanded=True):
        st.write(f"**Total events from API:** {len(df)}")
        st.write(f"**Columns:** {list(df.columns)}")
        st.write(f"**Sport events detected:** {df['_is_sport'].sum()}")
        st.dataframe(df.head(10))

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = df.copy()

if show_only_sports:
    filtered = filtered[filtered["_is_sport"]]

# Date window — only apply if we have real dates
today = date.today()
end   = today + timedelta(days=days_ahead)

has_date = filtered["_parsed_date"].notna()
if has_date.any():
    in_window = filtered["_parsed_date"].dt.tz_convert("US/Eastern").dt.date.apply(
        lambda d: today <= d <= end if pd.notna(d) else True
    )
    filtered = filtered[in_window | ~has_date]

# Search
if search:
    mask = (
        filtered.get("title", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
        filtered.get("event_ticker", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

# Deduplicate
if "event_ticker" in filtered.columns:
    filtered = filtered.drop_duplicates(subset=["event_ticker"])

# ── Metric strip ───────────────────────────────────────────────────────────────
total_all    = len(df)
total_sport  = int(df["_is_sport"].sum())
total_shown  = len(filtered)

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{total_all}</div></div>
  <div class="metric-box"><div class="metric-label">Sport markets</div><div class="metric-value">{total_sport}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{total_shown}</div></div>
  <div class="metric-box"><div class="metric-label">Window</div><div class="metric-value">+{days_ahead}d</div></div>
</div>
""", unsafe_allow_html=True)

# ── Cards ──────────────────────────────────────────────────────────────────────
if filtered.empty:
    sport_count = int(df["_is_sport"].sum())
    hint = ""
    if sport_count == 0:
        hint = "⚠️ Zero sport events detected. Try turning off <b>Sports events only</b> to see all markets — your API may use different ticker names."
    elif show_only_sports and sport_count > 0:
        hint = f"Found {sport_count} sport events but none match your date window. Try increasing the <b>Days ahead</b> slider."

    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">🔍</div>
        No events match your filters.<br><br>{hint}
    </div>""", unsafe_allow_html=True)

else:
    def get_icon(ticker):
        t = ticker.upper()
        if "NBA" in t:   return "🏀"
        if "MLB" in t:   return "⚾"
        if "NHL" in t:   return "🏒"
        if "NFL" in t:   return "🏈"
        if "GOLF" in t or "PGA" in t: return "⛳"
        if "TEN" in t or "ATP" in t or "WTA" in t: return "🎾"
        if "SOC" in t or "MLS" in t or "EPL" in t or "FIFA" in t: return "⚽"
        if "NCAAB" in t: return "🏀"
        if "NCAAF" in t: return "🏈"
        return "🏟️"

    def get_sport_label(ticker):
        t = ticker.upper()
        for league in ["NBA","MLB","NHL","NFL","PGA","ATP","WTA","MLS","EPL","NCAAB","NCAAF","FIFA","UEFA"]:
            if league in t:
                return league
        return "SPORT"

    cards_html = '<div class="card-grid">'
    for _, row in filtered.iterrows():
        try:
            ticker    = str(row.get("event_ticker", "")).upper()
            title_raw = str(row.get("title", "Unknown Event"))
            title     = title_raw.split(":")[-1].replace("Will the ","").split("?")[0].strip() or title_raw[:80]
            icon      = get_icon(ticker)
            label     = get_sport_label(ticker)

            d = row.get("_parsed_date")
            if pd.notna(d):
                try:
                    display_date = pd.Timestamp(d).tz_convert("US/Eastern").strftime("%b %d")
                except Exception:
                    display_date = "—"
            else:
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

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI SPORTS TERMINAL · DATA REFRESHES EVERY 3 MIN · NOT FINANCIAL ADVICE"
    "</p>",
    unsafe_allow_html=True
)
