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
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
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
.date-text { font-size: 11px; color: #6b7280; }
.card-icon { font-size: 20px; margin-bottom: 6px; display: block; }
.card-title { font-size: 14px; font-weight: 500; color: #e2e8f0; line-height: 1.45; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-footer { border-top: 1px solid #1a1a2e; padding-top: 10px; }
.ticker-text { font-size: 10px; color: #374151; letter-spacing: .06em; display: block; margin-bottom: 8px; }
.odds-row { display: flex; gap: 8px; }
.odds-yes { flex: 1; background: #0d2d1a; border: 1px solid #166534; border-radius: 6px; padding: 5px 8px; text-align: center; }
.odds-no  { flex: 1; background: #2d0d0d; border: 1px solid #7f1d1d; border-radius: 6px; padding: 5px 8px; text-align: center; }
.odds-label { font-size: 9px; color: #6b7280; text-transform: uppercase; letter-spacing: .08em; }
.odds-price-yes { font-size: 15px; font-weight: 500; color: #4ade80; }
.odds-price-no  { font-size: 15px; font-weight: 500; color: #f87171; }
.empty-state { text-align: center; padding: 80px 20px; color: #374151; font-size: 14px; }
hr { border-color: #1e1e32 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0f0f1a; border-bottom: 1px solid #1e1e32; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #4b5563; border: none; font-size: 12px; letter-spacing: .06em; }
.stTabs [aria-selected="true"] { background: #1e1e32 !important; color: #a5b4fc !important; border-radius: 6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
SPORT_CATS = {"sports"}

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_date(val):
    """Parse anything into a plain Python date, or return None."""
    try:
        if val is None or val == "":
            return None
        if isinstance(val, date) and not isinstance(val, pd.Timestamp):
            return val
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts):
            return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except Exception:
        return None

def fmt_date(d):
    try:
        if d is None:
            return "Open"
        return d.strftime("%b %d, %Y")
    except Exception:
        return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        pct = int(round(f * 100)) if f <= 1.0 else int(round(f))
        return f"{pct}%"
    except Exception:
        return "—"

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

# ── Fetch ──────────────────────────────────────────────────────────────────────
def paginate(with_markets=False, category=None):
    events, cursor = [], None
    for _ in range(30):
        try:
            kw = {"limit": 200, "status": "open"}
            if with_markets: kw["with_nested_markets"] = True
            if category:     kw["category"] = category
            if cursor:       kw["cursor"]   = cursor
            resp   = client.get_events(**kw).to_dict()
            batch  = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor") or (resp.get("pagination") or {}).get("next_cursor")
            if not cursor: break
            time.sleep(0.35)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

@st.cache_data(ttl=600)
def fetch_all():
    prog = st.progress(0, text="Fetching all events…")

    # Pass 1: all events, no markets (fast, complete)
    all_ev = paginate(with_markets=False)
    prog.progress(0.5, text=f"{len(all_ev)} events fetched. Getting sports odds…")

    # Pass 2: sports only WITH markets (for odds + close_time)
    sports_ev = paginate(with_markets=True, category="Sports")
    prog.empty()

    # Merge markets into pass-1 events
    mkt_map = {e["event_ticker"]: e.get("markets", []) for e in sports_ev if e.get("markets")}
    for e in all_ev:
        if e.get("event_ticker") in mkt_map:
            e["markets"] = mkt_map[e["event_ticker"]]

    if not all_ev:
        return pd.DataFrame()

    df = pd.DataFrame(all_ev).drop_duplicates(subset=["event_ticker"])

    # Category
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_is_sport"] = df["category"] == "Sports"

    # Extract odds from first nested market
    def extract(row):
        mkts = row.get("markets") or []
        if not mkts:
            return "—", "—", None
        m   = mkts[0]
        yes = fmt_pct(m.get("yes_bid_dollars") or m.get("yes_bid"))
        no  = fmt_pct(m.get("no_bid_dollars")  or m.get("no_bid"))
        # soonest close_time across all markets
        close = None
        for mk in mkts:
            d = safe_date(mk.get("close_time"))
            if d and (close is None or d < close):
                close = d
        return yes, no, close

    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"]   = info[0]
    df["_no"]    = info[1]
    df["_mkt_dt"]= info[2]   # plain date or None

    # Best sort date: strike_date > close_time > nested market close
    def best_dt(row):
        for col in ["strike_date", "close_time", "end_date", "expiration_time"]:
            d = safe_date(row.get(col))
            if d: return d
        return row.get("_mkt_dt")  # already a plain date or None

    df["_sort_dt"]    = df.apply(best_dt, axis=1)
    df["_display_dt"] = df["_sort_dt"].apply(fmt_date)

    return df

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")
    search = st.text_input("🔍 Search", placeholder="soccer, tennis, team…")

    st.markdown("---")
    st.markdown("**📅 Date Filter**")
    today = date.today()
    date_mode = st.radio("Show", ["All dates", "Today", "Tomorrow", "This week", "Custom range"], index=0)

    d_start = d_end = None
    if date_mode == "Today":
        d_start = d_end = today
    elif date_mode == "Tomorrow":
        d_start = d_end = today + timedelta(days=1)
    elif date_mode == "This week":
        d_start, d_end = today, today + timedelta(days=6)
    elif date_mode == "Custom range":
        d_start = st.date_input("From", value=today)
        d_end   = st.date_input("To",   value=today + timedelta(days=7))

    include_no_date = st.checkbox("Include events with no date", value=True)

    st.markdown("---")
    st.markdown("**↕️ Sort**")
    sort_by = st.radio("Order", ["Earliest first", "Latest first", "Default"], index=0)

    st.markdown("---")
    if st.button("🔄 Refresh"):
        fetch_all.clear()
        st.rerun()
    st.caption("Data cached 10 min.")

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")
with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data returned. Check API credentials.")
    st.stop()

# ── Filter ─────────────────────────────────────────────────────────────────────
filtered = df.copy()

# Date filter — sports always pass through (their dates live in nested markets)
if date_mode != "All dates":
    def date_ok(row):
        if row["_is_sport"]:
            return True          # never filter out sports
        d = row["_sort_dt"]
        if d is None:
            return include_no_date
        return d_start <= d <= d_end
    filtered = filtered[filtered.apply(date_ok, axis=1)]

# Search
if search:
    s = search.lower()
    mask = (
        filtered["title"].str.lower().str.contains(s, na=False) |
        filtered["event_ticker"].str.lower().str.contains(s, na=False) |
        filtered["category"].str.lower().str.contains(s, na=False)
    )
    filtered = filtered[mask]

# Sort
if sort_by != "Default":
    asc = sort_by == "Earliest first"
    has = filtered["_sort_dt"].notna()
    dated   = filtered[has].copy()
    undated = filtered[~has].copy()
    dated["_sk"] = dated["_sort_dt"].apply(lambda d: str(d) if d else "9999")
    dated = dated.sort_values("_sk", ascending=asc).drop(columns=["_sk"])
    filtered = pd.concat([dated, undated], ignore_index=True)

# ── Metrics ────────────────────────────────────────────────────────────────────
all_cats    = sorted(df["category"].unique().tolist())
non_sport   = [c for c in all_cats if c.lower() not in SPORT_CATS]
tab_labels  = ["All", "Sports"] + non_sport
sport_count = int(df["_is_sport"].sum())

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
  <div class="metric-box"><div class="metric-label">Categories</div><div class="metric-value">{len(all_cats)}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Card helpers ───────────────────────────────────────────────────────────────
def get_icon(ticker, cat):
    t, c = ticker.upper(), cat.lower()
    if "NBA" in t or "NCAAB" in t:                          return "🏀"
    if "MLB" in t:                                           return "⚾"
    if "NHL" in t:                                           return "🏒"
    if "NFL" in t or "NCAAF" in t:                          return "🏈"
    if "GOLF" in t or "PGA" in t:                           return "⛳"
    if "TEN" in t or "ATP" in t or "WTA" in t:              return "🎾"
    if any(x in t for x in ["SOC","MLS","EPL","FIFA","UEFA"]): return "⚽"
    if "UFC" in t or "MMA" in t:                            return "🥊"
    if "F1" in t or "NASCAR" in t or "MOTOR" in t:          return "🏎️"
    if "CRICKET" in t or "IPL" in t:                        return "🏏"
    if "RUGBY" in t:                                         return "🏉"
    if "BOX" in t:                                           return "🥊"
    if "CHESS" in t:                                         return "♟️"
    if "DART" in t:                                          return "🎯"
    if "basketball" in c:  return "🏀"
    if "soccer" in c:      return "⚽"
    if "tennis" in c:      return "🎾"
    if "baseball" in c:    return "⚾"
    if "hockey" in c:      return "🏒"
    if "football" in c:    return "🏈"
    if "golf" in c:        return "⛳"
    if "sport" in c:       return "🏟️"
    if "election" in c:    return "🗳️"
    if "politic" in c:     return "🗳️"
    if "financ" in c or "econom" in c or "crypto" in c: return "📈"
    if "entertain" in c:   return "🎬"
    if "climate" in c or "weather" in c: return "🌍"
    if "science" in c or "tech" in c:   return "🔬"
    if "health" in c:      return "🏥"
    return "📊"

def get_pill(cat):
    c = cat.lower().strip()
    if c in SPORT_CATS: return "cat-Sports"
    m = {"politics":"cat-Politics","elections":"cat-Elections","financials":"cat-Financials",
         "entertainment":"cat-Entertainment","climate and weather":"cat-Climate",
         "science and technology":"cat-Science","health":"cat-Health"}
    return m.get(c, "cat-default")

def detect_sport(ticker):
    t = ticker.upper()
    if "NBA" in t or "NCAAB" in t: return "Basketball"
    if "MLB" in t:                  return "Baseball"
    if "NHL" in t:                  return "Hockey"
    if "NFL" in t or "NCAAF" in t: return "Football"
    if any(x in t for x in ["SOC","MLS","EPL","UEFA","FIFA"]): return "Soccer"
    if "TEN" in t or "ATP" in t or "WTA" in t: return "Tennis"
    if "GOLF" in t or "PGA" in t:  return "Golf"
    if "UFC" in t or "MMA" in t:   return "MMA"
    if "CRICKET" in t or "IPL" in t: return "Cricket"
    if "F1" in t or "NASCAR" in t or "MOTOR" in t: return "Motorsport"
    if "BOX" in t:    return "Boxing"
    if "RUGBY" in t:  return "Rugby"
    if "DART" in t:   return "Darts"
    if "CHESS" in t:  return "Chess"
    if "AFL" in t or "AUSSIE" in t: return "Aussie Rules"
    return "Other"

SPORT_ICONS = {
    "Basketball":"🏀","Baseball":"⚾","Hockey":"🏒","Football":"🏈",
    "Soccer":"⚽","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉","Darts":"🎯",
    "Chess":"♟️","Aussie Rules":"🏉","Other":"🏟️",
}

def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets match your filters.</div>', unsafe_allow_html=True)
        return
    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker  = str(row.get("event_ticker","")).upper()
            cat     = str(row.get("category","Other"))
            raw     = str(row.get("title","Unknown"))
            title   = raw.split(":")[-1].replace("Will the ","").split("?")[0].strip() or raw[:80]
            icon    = get_icon(ticker, cat)
            pill    = get_pill(cat)
            label   = cat[:14]
            dt      = str(row.get("_display_dt","Open"))
            yes     = str(row.get("_yes","—"))
            no      = str(row.get("_no","—"))

            html += f"""
            <div class="market-card">
                <div class="card-top">
                    <span class="cat-pill {pill}">{label}</span>
                    <span class="date-text">📅 {dt}</span>
                </div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">
                    <span class="ticker-text">{ticker}</span>
                    <div class="odds-row">
                        <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{yes}</div></div>
                        <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{no}</div></div>
                    </div>
                </div>
            </div>"""
        except Exception:
            continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs(tab_labels)
for i, tab in enumerate(tabs):
    with tab:
        cat = tab_labels[i]
        if cat == "All":
            render_cards(filtered)
        elif cat == "Sports":
            sdf = filtered[filtered["_is_sport"]].copy()
            sdf["_sport_type"] = sdf["event_ticker"].apply(detect_sport)
            present = sorted(sdf["_sport_type"].unique().tolist())
            sub_labels = ["All Sports"] + [f"{SPORT_ICONS.get(s,'🏟️')} {s}" for s in present]
            sub_tabs = st.tabs(sub_labels)
            for j, stab in enumerate(sub_tabs):
                with stab:
                    if j == 0:
                        render_cards(sdf)
                    else:
                        render_cards(sdf[sdf["_sport_type"] == present[j-1]])
        else:
            render_cards(filtered[filtered["category"] == cat])

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
