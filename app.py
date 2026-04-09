import streamlit as st
import pandas as pd
import tempfile
import time
import requests
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="🏟️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
.stApp { background: #0a0a0f; }
section[data-testid="stSidebar"] { background: #0f0f1a !important; border-right: 1px solid #1e1e32; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: #6b7280 !important; font-size: 11px !important; letter-spacing: .08em; text-transform: uppercase; }
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
.cat-pill { font-size: 10px; font-weight: 500; letter-spacing: .1em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; border: 1px solid; }
.cat-Sports        { background: #1a2e1a; color: #4ade80; border-color: #166534; }
.cat-Politics      { background: #1e1a2e; color: #818cf8; border-color: #3730a3; }
.cat-Elections     { background: #2e1a1e; color: #f472b6; border-color: #9d174d; }
.cat-Financials    { background: #2e2a1a; color: #fbbf24; border-color: #92400e; }
.cat-Entertainment { background: #2e1e1a; color: #fb923c; border-color: #9a3412; }
.cat-Climate       { background: #1a2e2e; color: #22d3ee; border-color: #164e63; }
.cat-Science       { background: #1e2e1a; color: #86efac; border-color: #14532d; }
.cat-Health        { background: #2e1a2e; color: #e879f9; border-color: #701a75; }
.cat-default       { background: #1e1e32; color: #94a3b8; border-color: #2d2d55; }
.date-text { font-size: 11px; color: #374151; }
.card-title { font-size: 15px; font-weight: 500; color: #e2e8f0; line-height: 1.45; margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-icon { font-size: 22px; margin-bottom: 8px; display: block; }
.card-footer { border-top: 1px solid #1a1a2e; padding-top: 10px; margin-top: auto; }
.ticker-text { font-size: 10px; color: #374151; letter-spacing: .06em; display: block; margin-bottom: 8px; }
.odds-row { display: flex; gap: 8px; }
.odds-yes { flex: 1; background: #0d2d1a; border: 1px solid #166534; border-radius: 6px; padding: 6px 8px; text-align: center; }
.odds-no  { flex: 1; background: #2d0d0d; border: 1px solid #7f1d1d; border-radius: 6px; padding: 6px 8px; text-align: center; }
.odds-label { font-size: 9px; color: #6b7280; text-transform: uppercase; letter-spacing: .08em; }
.odds-price-yes { font-size: 16px; font-weight: 500; color: #4ade80; }
.odds-price-no  { font-size: 16px; font-weight: 500; color: #f87171; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.empty-state { text-align: center; padding: 80px 20px; color: #374151; font-size: 14px; }
hr { border-color: #1e1e32 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0f0f1a; border-bottom: 1px solid #1e1e32; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #4b5563; border: none; font-size: 12px; letter-spacing: .06em; }
.stTabs [aria-selected="true"] { background: #1e1e32 !important; color: #a5b4fc !important; border-radius: 6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
UTC = timezone.utc

KALSHI_SPORT_CATS = {"sports"}

def parse_date_safe(val):
    try:
        if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
            return None
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().astimezone(UTC).date()
    except Exception:
        return None

# ── API client ─────────────────────────────────────────────────────────────────
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
        st.error(f"❌ Connection failed: {e}")
        st.stop()

client = get_client()

# ── Step 1: Get available sports from Kalshi's own filters endpoint ────────────
@st.cache_data(ttl=3600)
def fetch_sport_filters():
    """Call /search/filters_by_sport to get the exact sport names Kalshi uses."""
    try:
        resp = requests.get(f"{BASE_URL}/search/filters_by_sport", timeout=10)
        data = resp.json()
        filters = data.get("filters_by_sports", {})
        ordering = data.get("sport_ordering", list(filters.keys()))
        return filters, ordering
    except Exception as e:
        return {}, []

# ── Step 2: Fetch all events with pagination ───────────────────────────────────
def paginate_events(with_markets=False, category=None):
    """Paginate through Kalshi events. Returns list of raw event dicts."""
    all_events = []
    cursor     = None
    MAX_PAGES  = 30
    DELAY      = 0.35

    for page in range(MAX_PAGES):
        try:
            kwargs = {"limit": 200, "status": "open"}
            if with_markets:
                kwargs["with_nested_markets"] = True
            if category:
                kwargs["category"] = category
            if cursor:
                kwargs["cursor"] = cursor

            resp   = client.get_events(**kwargs)
            data   = resp.to_dict()
            events = data.get("events", [])
            if not events:
                break

            all_events.extend(events)

            cursor = (
                data.get("cursor") or
                data.get("next_cursor") or
                (data.get("pagination") or {}).get("next_cursor")
            )
            if not cursor:
                break

            time.sleep(DELAY)

        except Exception as e:
            err = str(e)
            if "429" in err or "too_many_requests" in err.lower():
                time.sleep(3)
                continue
            else:
                break

    return all_events


@st.cache_data(ttl=600)
def fetch_all_events():
    progress = st.progress(0, text="Pass 1: fetching all events…")

    # Pass 1 — fetch ALL events fast (no nested markets) for complete coverage
    all_events = paginate_events(with_markets=False)
    progress.progress(0.5, text=f"Pass 1 done: {len(all_events)} events. Pass 2: fetching sports odds…")

    # Pass 2 — fetch Sports events WITH nested markets for odds + close_time
    sports_with_markets = paginate_events(with_markets=True, category="Sports")
    progress.progress(1.0, text="Done!")
    progress.empty()

    # Build a lookup of event_ticker -> markets from pass 2
    markets_lookup = {}
    for e in sports_with_markets:
        ticker = e.get("event_ticker")
        if ticker and e.get("markets"):
            markets_lookup[ticker] = e["markets"]

    # Merge markets into pass 1 events
    for e in all_events:
        ticker = e.get("event_ticker")
        if ticker in markets_lookup:
            e["markets"] = markets_lookup[ticker]

    if not all_events:
        return pd.DataFrame()

    df = pd.DataFrame(all_events)
    if "event_ticker" in df.columns:
        df = df.drop_duplicates(subset=["event_ticker"])

    if "category" not in df.columns:
        df["category"] = "Other"
    df["category"] = df["category"].fillna("Other").str.strip()
    df["_is_sport"] = df["category"].str.strip() == "Sports"

    # ── Price formatter ────────────────────────────────────────────────────────
    def fmt_price(v):
        try:
            f = float(v)
            pct = int(round(f * 100)) if f <= 1 else int(round(f))
            return f"{pct}%"
        except Exception:
            return "—"

    # ── Extract odds + best close_time from nested markets ────────────────────
    def extract_odds(row):
        markets = row.get("markets") or []
        if not markets or not isinstance(markets, list):
            return "—", "—", None
        # Pick the market with the soonest close_time
        best_market = markets[0]
        best_close  = None
        for m in markets:
            cd = parse_date_safe(m.get("close_time"))
            if cd is not None and (best_close is None or cd < best_close):
                best_close   = cd
                best_market  = m
        yes = fmt_price(best_market.get("yes_bid_dollars") or best_market.get("yes_bid"))
        no  = fmt_price(best_market.get("no_bid_dollars")  or best_market.get("no_bid"))
        return yes, no, best_close

    odds_info        = df.apply(extract_odds, axis=1, result_type="expand")
    df["_yes_price"] = odds_info[0]
    df["_no_price"]  = odds_info[1]
    df["_close_date"]= odds_info[2]  # plain Python date or None

    # ── Build _sort_date — used for sorting (date object) ─────────────────────
    date_cols = ["strike_date", "end_date", "close_time", "expiration_time"]

    def get_sort_date(row):
        # Try top-level fields first
        for col in date_cols:
            d = parse_date_safe(row.get(col))
            if d is not None:
                return d
        # Fall back to close_time from nested markets
        return row.get("_close_date")

    df["_sort_date"]    = df.apply(get_sort_date, axis=1)
    def fmt_date(d):
        try:
            if d is None or str(d) in ("NaT", "None", "nan"):
                return "Open"
            return d.strftime("%b %d, %Y")
        except Exception:
            return "Open"
    df["_display_date"] = df["_sort_date"].apply(fmt_date)

    return df

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")

    search = st.text_input("🔍 Search", placeholder="soccer, tennis, team…")

    st.markdown("---")
    st.markdown("**📅 Date Filter**")
    today = date.today()

    date_mode = st.radio(
        "Show markets",
        ["All dates", "Today", "Tomorrow", "This week", "Custom range"],
        index=0,
    )

    custom_start = None
    custom_end   = None

    if date_mode == "Today":
        custom_start = today
        custom_end   = today
    elif date_mode == "Tomorrow":
        custom_start = today + timedelta(days=1)
        custom_end   = today + timedelta(days=1)
    elif date_mode == "This week":
        custom_start = today
        custom_end   = today + timedelta(days=6)
    elif date_mode == "Custom range":
        custom_start = st.date_input("From", value=today)
        custom_end   = st.date_input("To",   value=today + timedelta(days=7))

    include_no_date = st.checkbox("Include markets with no date", value=True)

    st.markdown("---")
    st.markdown("**↕️ Sort**")
    sort_by = st.radio("Order by", ["Date (earliest first)", "Date (latest first)", "Default"], index=0)

    st.markdown("---")
    if st.button("🔄 Refresh data"):
        fetch_all_events.clear()
        fetch_sport_filters.clear()
        st.rerun()
    st.caption("Cached 10 min to avoid rate limits.")

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")

# Fetch sport filters to understand what categories exist
sport_filters, sport_ordering = fetch_sport_filters()

with st.spinner("Loading all markets…"):
    df = fetch_all_events()

if df.empty:
    st.markdown('<div class="empty-state">No data returned. Check your API credentials.</div>', unsafe_allow_html=True)
    st.stop()

# Show what sport categories were found (helpful for debugging)
all_cats = df["category"].value_counts()
sport_cats = [c for c in all_cats.index if "sport" in c.lower()]

# ── Apply filters ──────────────────────────────────────────────────────────────
filtered = df.copy()

if date_mode != "All dates":
    def date_ok(row):
        # Sports events always show — their dates are often missing or in nested markets
        if row.get("_is_sport"):
            return True
        d = row.get("_sort_date")
        if d is None:
            return include_no_date
        return custom_start <= d <= custom_end
    filtered = filtered[filtered.apply(date_ok, axis=1)]

if search:
    mask = (
        filtered.get("title", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
        filtered.get("event_ticker", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
        filtered.get("category", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

# ── Sort ──────────────────────────────────────────────────────────────────────
if sort_by != "Default":
    ascending    = sort_by == "Date (earliest first)"
    has_date     = filtered["_sort_date"].notna()
    with_date    = filtered[has_date].copy().sort_values("_sort_date", ascending=ascending)
    without_date = filtered[~has_date].copy()
    filtered     = pd.concat([with_date, without_date], ignore_index=True)

# ── Metrics ────────────────────────────────────────────────────────────────────
# Count sports using all sport-related categories found
sport_count    = int(filtered["_is_sport"].sum())
# Always build tabs from full dataset so they don't disappear when filters narrow results
all_categories = sorted(df["category"].unique().tolist())
non_sport_cats = [c for c in all_categories if c.lower().strip() not in KALSHI_SPORT_CATS]
tab_labels     = ["All", "Sports"] + non_sport_cats
categories     = all_categories

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
  <div class="metric-box"><div class="metric-label">Categories</div><div class="metric-value">{len(categories)}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_icon(ticker, category):
    t = ticker.upper()
    c = str(category).lower()
    if "NBA"    in t: return "🏀"
    if "MLB"    in t: return "⚾"
    if "NHL"    in t: return "🏒"
    if "NFL"    in t: return "🏈"
    if "GOLF"   in t or "PGA"  in t: return "⛳"
    if "TEN"    in t or "ATP"  in t or "WTA" in t: return "🎾"
    if "SOC"    in t or "MLS"  in t or "EPL" in t or "FIFA" in t or "UEFA" in t: return "⚽"
    if "UFC"    in t or "MMA"  in t: return "🥊"
    if "F1"     in t or "NASCAR" in t: return "🏎️"
    if "NCAAB"  in t: return "🏀"
    if "NCAAF"  in t: return "🏈"
    if "soccer" in c or "football" in c: return "⚽"
    if "tennis" in c: return "🎾"
    if "basketball" in c: return "🏀"
    if "baseball" in c: return "⚾"
    if "hockey" in c: return "🏒"
    if "golf"   in c: return "⛳"
    if "sport"  in c: return "🏟️"
    if "election" in c or "polit" in c: return "🗳️"
    if "financ" in c or "econom" in c: return "📈"
    if "entertain" in c: return "🎬"
    if "climate" in c or "weather" in c: return "🌍"
    if "science" in c or "tech" in c: return "🔬"
    if "health" in c: return "🏥"
    return "📊"

def get_pill_class(category):
    c = str(category).lower().strip()
    if c in KALSHI_SPORT_CATS: return "cat-Sports"
    mapping = {
        "politics":               "cat-Politics",
        "elections":              "cat-Elections",
        "financials":             "cat-Financials",
        "entertainment":          "cat-Entertainment",
        "climate and weather":    "cat-Climate",
        "science and technology": "cat-Science",
        "health":                 "cat-Health",
    }
    return mapping.get(c, "cat-default")

def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets match your filters.</div>', unsafe_allow_html=True)
        return

    cards_html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker       = str(row.get("event_ticker", "")).upper()
            category     = str(row.get("category", "Other"))
            title_raw    = str(row.get("title", "Unknown"))
            title        = title_raw.split(":")[-1].replace("Will the ", "").split("?")[0].strip() or title_raw[:80]
            icon         = get_icon(ticker, category)
            pill_cls     = get_pill_class(category)
            cat_label    = category[:14]
            display_date = str(row.get("_display_date", "Open"))
            yes_price    = str(row.get("_yes_price", "—"))
            no_price     = str(row.get("_no_price",  "—"))

            cards_html += f"""
            <div class="market-card">
                <div class="card-top">
                    <span class="cat-pill {pill_cls}">{cat_label}</span>
                    <span class="date-text">📅 {display_date}</span>
                </div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">
                    <span class="ticker-text">{ticker}</span>
                    <div class="odds-row">
                        <div class="odds-yes">
                            <div class="odds-label">YES</div>
                            <div class="odds-price-yes">{yes_price}</div>
                        </div>
                        <div class="odds-no">
                            <div class="odds-label">NO</div>
                            <div class="odds-price-no">{no_price}</div>
                        </div>
                    </div>
                </div>
            </div>"""
        except Exception:
            continue
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs(tab_labels)
for i, tab in enumerate(tabs):
    with tab:
        cat = tab_labels[i]
        if cat == "All":
            render_cards(filtered)
        elif cat == "Sports":
            sports_df = filtered[filtered["_is_sport"]]

            # Build sub-tabs from sport series_ticker prefixes
            SPORT_ICONS = {
                "Basketball": "🏀", "Baseball": "⚾", "Hockey": "🏒",
                "Football": "🏈", "Soccer": "⚽", "Tennis": "🎾",
                "Golf": "⛳", "MMA": "🥊", "Cricket": "🏏",
                "Esports": "🎮", "Motorsport": "🏎️", "Boxing": "🥊",
                "Rugby": "🏉", "Lacrosse": "🥍", "Darts": "🎯",
                "Chess": "♟️", "Aussie Rules": "🏉", "Other": "🏟️",
            }

            # Detect sport type from series_ticker
            def detect_sport(ticker):
                t = str(ticker).upper()
                if "NBA" in t or "NCAAB" in t: return "Basketball"
                if "MLB" in t or "NCAAB" in t: return "Baseball"
                if "NHL" in t: return "Hockey"
                if "NFL" in t or "NCAAF" in t: return "Football"
                if "SOC" in t or "MLS" in t or "EPL" in t or "UEFA" in t or "FIFA" in t: return "Soccer"
                if "TEN" in t or "ATP" in t or "WTA" in t: return "Tennis"
                if "GOLF" in t or "PGA" in t: return "Golf"
                if "MMA" in t or "UFC" in t: return "MMA"
                if "CRICKET" in t or "IPL" in t: return "Cricket"
                if "ESPORT" in t or "LOL" in t or "DOTA" in t or "CSGO" in t: return "Esports"
                if "F1" in t or "NASCAR" in t or "MOTOR" in t: return "Motorsport"
                if "BOX" in t: return "Boxing"
                if "RUGBY" in t: return "Rugby"
                if "LAX" in t or "LACROSSE" in t: return "Lacrosse"
                if "DART" in t: return "Darts"
                if "CHESS" in t: return "Chess"
                if "AFL" in t or "AUSSIE" in t: return "Aussie Rules"
                return "Other"

            sports_df = sports_df.copy()
            sports_df["_sport_type"] = sports_df["event_ticker"].apply(detect_sport)

            # Only show sport types that have events
            present_sports = sorted(sports_df["_sport_type"].unique().tolist())
            sport_sub_labels = ["All Sports"] + [
                f"{SPORT_ICONS.get(s, '🏟️')} {s}" for s in present_sports
            ]

            sub_tabs = st.tabs(sport_sub_labels)
            for j, sub_tab in enumerate(sub_tabs):
                with sub_tab:
                    if j == 0:
                        render_cards(sports_df)
                    else:
                        sport_name = present_sports[j - 1]
                        render_cards(sports_df[sports_df["_sport_type"] == sport_name])
        else:
            render_cards(filtered[filtered["category"] == cat])

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
