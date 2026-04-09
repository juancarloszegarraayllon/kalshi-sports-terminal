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
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #6b7280 !important; font-size: 11px !important; letter-spacing: .08em; text-transform: uppercase; }
h1 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; color: #f0f0ff !important; letter-spacing: -.02em; font-size: 2.2rem !important; }
.metric-strip { display: flex; gap: 12px; margin-bottom: 28px; flex-wrap: wrap; }
.metric-box { background: #0f0f1a; border: 1px solid #1e1e32; border-radius: 10px; padding: 14px 20px; flex: 1; min-width: 120px; }
.metric-label { font-size: 10px; color: #4b5563; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 500; color: #a5b4fc; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.market-card { background: #0f0f1a; border: 1px solid #1e1e32; border-radius: 12px; padding: 18px 20px; position: relative; overflow: hidden; transition: border-color .2s, transform .15s; }
.market-card:hover { border-color: #4f46e5; transform: translateY(-2px); }
.market-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,#4f46e5,#818cf8); opacity:0; transition:opacity .2s; }
.market-card:hover::before { opacity:1; }
.card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.cat-pill { font-size:10px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; padding:3px 10px; border-radius:4px; border:1px solid; white-space:nowrap; }
.pill-sports       { background:#1a2e1a; color:#4ade80; border-color:#166534; }
.pill-elections    { background:#2e1a1e; color:#f472b6; border-color:#9d174d; }
.pill-politics     { background:#1e1a2e; color:#818cf8; border-color:#3730a3; }
.pill-economics    { background:#2e2a1a; color:#fbbf24; border-color:#92400e; }
.pill-financials   { background:#2e2a1a; color:#fb923c; border-color:#9a3412; }
.pill-crypto       { background:#1e2a2e; color:#67e8f9; border-color:#0e7490; }
.pill-companies    { background:#2e1e2e; color:#d8b4fe; border-color:#7e22ce; }
.pill-entertainment{ background:#2e1e1a; color:#fdba74; border-color:#c2410c; }
.pill-climate      { background:#1a2e2e; color:#22d3ee; border-color:#164e63; }
.pill-science      { background:#1e2e1a; color:#86efac; border-color:#14532d; }
.pill-health       { background:#2e1a2e; color:#e879f9; border-color:#701a75; }
.pill-social       { background:#2e1e2a; color:#f9a8d4; border-color:#9d174d; }
.pill-world        { background:#1a1e2e; color:#93c5fd; border-color:#1e40af; }
.pill-default      { background:#1e1e32; color:#94a3b8; border-color:#2d2d55; }
.date-text { font-size:11px; color:#6b7280; }
.card-icon { font-size:20px; margin-bottom:6px; display:block; }
.card-title { font-size:14px; font-weight:500; color:#e2e8f0; line-height:1.45; margin-bottom:12px; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; min-height:58px; }
.card-footer { border-top:1px solid #1a1a2e; padding-top:10px; }
.ticker-text { font-size:10px; color:#374151; letter-spacing:.06em; display:block; margin-bottom:8px; }
.odds-row { display:flex; gap:8px; }
.odds-yes { flex:1; background:#0d2d1a; border:1px solid #166534; border-radius:6px; padding:5px 8px; text-align:center; }
.odds-no  { flex:1; background:#2d0d0d; border:1px solid #7f1d1d; border-radius:6px; padding:5px 8px; text-align:center; }
.odds-label { font-size:9px; color:#6b7280; text-transform:uppercase; letter-spacing:.08em; }
.odds-price-yes { font-size:15px; font-weight:500; color:#4ade80; }
.odds-price-no  { font-size:15px; font-weight:500; color:#f87171; }
.empty-state { text-align:center; padding:80px 20px; color:#374151; font-size:14px; }
hr { border-color:#1e1e32 !important; }
.stTabs [data-baseweb="tab-list"] { background:#0f0f1a; border-bottom:1px solid #1e1e32; gap:2px; flex-wrap:wrap; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#4b5563; border:none; font-size:12px; letter-spacing:.04em; padding:8px 12px; }
.stTabs [aria-selected="true"] { background:#1e1e32 !important; color:#a5b4fc !important; border-radius:6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ── Exact Kalshi structure ─────────────────────────────────────────────────────
# Top-level categories in Kalshi's order
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":                 ("🏟️","pill-sports"),
    "Elections":              ("🗳️","pill-elections"),
    "Politics":               ("🏛️","pill-politics"),
    "Economics":              ("📈","pill-economics"),
    "Financials":             ("💰","pill-financials"),
    "Crypto":                 ("₿", "pill-crypto"),
    "Companies":              ("🏢","pill-companies"),
    "Entertainment":          ("🎬","pill-entertainment"),
    "Climate and Weather":    ("🌍","pill-climate"),
    "Science and Technology": ("🔬","pill-science"),
    "Health":                 ("🏥","pill-health"),
    "Social":                 ("👥","pill-social"),
    "World":                  ("🌐","pill-world"),
    "Transportation":         ("✈️","pill-default"),
    "Mentions":               ("💬","pill-default"),
}

CAT_TAGS = {
    "Elections":           ["US Elections","Primaries","House","International elections"],
    "Politics":            ["Trump","Congress","International","SCOTUS & courts","Recurring","Local","Iran"],
    "Economics":           ["Growth","Inflation","Oil and energy","Jobs & Economy","Fed","GDP","Global Central Banks","Housing"],
    "Financials":          ["Agriculture","Oil & Gas","Metals","S&P","Nasdaq","Daily","Treasuries","EUR/USD","USD/JPY"],
    "Crypto":              ["BTC","ETH","SOL","DOGE","BNB","HYPE","XRP","15 min","Hourly","Pre-Market"],
    "Companies":           ["IPOs","Product launches","KPIs","Elon Musk","CEOs","Layoffs"],
    "Entertainment":       ["Music","Television","Awards","Movies","Music charts","Oscars","Video games","Rotten Tomatoes"],
    "Climate and Weather": ["Daily temperature","Snow and rain","Climate change","Natural disasters","Hurricanes","Hourly temperature"],
    "Science and Technology":["AI","Energy","Medicine","Space"],
    "Health":              ["Diseases"],
    "Mentions":            ["Earnings","Politicians","Sports"],
}

# ── Sports structure: (icon, sport_name, [series_tickers...]) ──────────────────
# Series tickers confirmed from Kalshi's API + sports filter docs
SPORTS = [
    ("🏀","Basketball",[
        "KXNBA","NBA","WNBA","KXWNBA","KXNCAAB","NCAAB",
        "EUROLEAGUE","ABA","CBABASKET","BBL","ISRAELBASKET",
        "ITALYBASKET","JAPANB","LNB","LIGABASKET","VTBLEAGUE","SPAINACB","BSL",
    ]),
    ("⚾","Baseball",[
        "MLB","KXMLB","NCAAB","JAPANNPB","NPB","KOREAKBO","KBO","COLLEGEBASEBALL",
    ]),
    ("🎾","Tennis",[
        "ATP","WTA","KXATP","KXWTA",
        "ATPMONTECARLO","MONTECARLO","ATPFRENCHOPEN","WTAFRENCHOPEN",
        "FRENCHOPEN","ROLANDGARROS","ATPCHALLENGERMA","ATPCHALLENGERMO","ATPCHALLENGERW",
        "WTA125KMADRID","CHALLMADRID","CHALLMONZA","CHALLWUNING",
    ]),
    ("⚽","Soccer",[
        "EPL","KXEPL","MLS","KXMLS","LALIGA","SERIEA","BUNDESLIGA","LIGUE1",
        "UCL","UEL","UECL","CHAMPIONSLEAGUE","EUROPALEAGUE","CONFERENCELEAGUE",
        "LIGAMX","BRASILEIRAO","EREDIVISIE","LIGAPORTUGAL","BELGIANPRO",
        "ALLSVENSKAN","SUPERLIGA","EFLCHAMP","SUPERLIG","SWISSSUPER",
        "SCOTTISH","SCOTTISHPREM","KOREAKLEAGUE","JAPANJ1","CHINESESUPER",
        "CONCACAF","LIBERTADORES","SUDAMERICANA","COPADELREY","COPPA","DFBPOKAL",
        "FACUP","FIFA","WORLDCUP","WOMENSCL","BUNDESLIGA2","LALIGA2","SERIEB",
        "USLCHAMP","URUGUAY","CHILE","ECUADOR","VENEZUELA","COLOMBIA",
        "ARGENTINA","AUSTRALIALEAGUE","THAI","EGYPT","CROATIA","EKSTRAKLASA",
        "GREECE","KNVB","LIGA1PERU","APF","BALLER","SAUDIPL","SAUDI",
    ]),
    ("🏒","Hockey",[
        "NHL","KXNHL","AHL","FINLANDLIIGA","LIIGA","CZECHEXTRA","EXTRALIGA",
        "GERMDEL","DEL","KHL","SHL","SWISSNL","COLLEGEHOCKEY",
    ]),
    ("⛳","Golf",[
        "MASTERS","KXMASTERS","THEGOLFMASTERS","RYDERCUP","KXRYDERCUP",
        "PGA","KXPGA","TOUR","KXPGACURRY","KXPGARYDER","KXSCOTTIESLAM",
    ]),
    ("🥊","MMA",[
        "UFC","KXUFC","MMA","KXMMA","KXMCGREGORFIGHTNEXT",
    ]),
    ("🏏","Cricket",[
        "IPL","KXIPL","PSL","KXPSL","T20I","T20INT","BBL","KXBBL",
    ]),
    ("🏈","Football",[
        "NFL","KXNFL","NCAAF","KXNCAAF","UFL","KXUFL",
        "KXNFLMVP","KXSB","KXNFLPLAYOFF","KXNFLCOTY",
    ]),
    ("🎮","Esports",[
        "CS2","LOL","DOTA","DOTA2","VAL","VALORANT","OW","OVERWATCH",
        "R6","RAINBOW","ESPORT","KXESPORT",
    ]),
    ("🏎️","Motorsport",[
        "F1","KXF1","KXF1RETIRE","NASCAR","KXNASCAR","NASCARCUP",
        "NASCAROREILLY","NASCARTRUCK","INDYCAR","MOTOGP","KXMOTOGP",
    ]),
    ("🏉","Aussie Rules",[
        "AFL","KXAFL",
    ]),
    ("🥊","Boxing",[
        "BOX","BOXING","KXBOX","KXBOXING",
    ]),
    ("🥍","Lacrosse",[
        "LACROSSE","LAX","NLL","PLL","COLLEGELAX",
    ]),
    ("🏉","Rugby",[
        "NRL","RUGBY","KXNRL","FRENCHRUGBY","TOP14","GALLAGHER","SUPERLEAGUE",
    ]),
    ("🎯","Darts",[
        "PDC","DART","KXDART","PREMIERLEAGUEDARTS",
    ]),
    ("♟️","Chess",[
        "CHESS","FIDE","KXCHESS",
    ]),
]

SPORT_ICON  = {s: ic for ic,s,_ in SPORTS}
SPORT_TICKS = {s: ticks for _,s,ticks in SPORTS}

def detect_sport(series_ticker, event_ticker=""):
    combined = (str(series_ticker) + " " + str(event_ticker)).upper()
    for _, sport, tickers in SPORTS:
        for t in tickers:
            if t.upper() in combined:
                return sport
    return "Other"

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_date(val):
    try:
        if val is None or val == "": return None
        if isinstance(val, date) and not isinstance(val, pd.Timestamp): return val
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except Exception: return None

def fmt_date(d):
    try: return d.strftime("%b %d, %Y") if d else "Open"
    except: return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f<=1.0 else int(round(f))}%"
    except: return "—"

# ── API ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        key_id  = st.secrets["KALSHI_API_KEY_ID"]
        key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(key_str); pem = f.name
        cfg = Configuration()
        cfg.api_key_id = key_id
        cfg.private_key_pem_path = pem
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"❌ {e}"); st.stop()

client = get_client()

def fetch_by_series(series_ticker, with_markets=False):
    """Fetch all open events for a given series_ticker."""
    events, cursor = [], None
    for _ in range(10):
        try:
            kw = {"limit": 200, "status": "open", "series_ticker": series_ticker}
            if with_markets: kw["with_nested_markets"] = True
            if cursor: kw["cursor"] = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.2)
        except Exception as e:
            if "429" in str(e): time.sleep(2)
            else: break
    return events

def fetch_general(with_markets=False, category=None):
    """Paginate general events endpoint."""
    events, cursor = [], None
    for _ in range(30):
        try:
            kw = {"limit": 200, "status": "open"}
            if with_markets: kw["with_nested_markets"] = True
            if category:     kw["category"] = category
            if cursor:       kw["cursor"]   = cursor
            resp  = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
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
    prog = st.progress(0, text="Step 1: Fetching all non-sport events…")

    # ── Pass 1: ALL events (general pagination) ────────────────────────────────
    all_events = fetch_general(with_markets=False)
    prog.progress(0.25, text=f"{len(all_events)} events. Step 2: Fetching live sports by series…")

    # ── Pass 2: Fetch live sports events by series ticker ─────────────────────
    # Collect all sport series tickers and fetch events for each
    all_sport_tickers = []
    for _, sport, tickers in SPORTS:
        all_sport_tickers.extend(tickers)

    sports_events = []
    seen_tickers  = {e.get("event_ticker") for e in all_events}

    total = len(all_sport_tickers)
    for i, series in enumerate(all_sport_tickers):
        prog.progress(0.25 + 0.5*(i/total), text=f"Fetching {series}…")
        ev = fetch_by_series(series, with_markets=True)
        for e in ev:
            t = e.get("event_ticker")
            if t and t not in seen_tickers:
                e["_series_used"] = series
                sports_events.append(e)
                seen_tickers.add(t)

    prog.progress(0.75, text=f"Found {len(sports_events)} new sports events. Step 3: Fetching sports odds…")

    # ── Pass 3: Get odds for general events that are sports ────────────────────
    sport_futures = [e for e in all_events if e.get("category") == "Sports"]
    sport_futures_with_mkts = fetch_general(with_markets=True, category="Sports")
    mkt_map = {e["event_ticker"]: e.get("markets",[]) for e in sport_futures_with_mkts if e.get("markets")}

    # Apply markets to sports_events too
    for e in sports_events:
        t = e.get("event_ticker","")
        if t in mkt_map and not e.get("markets"):
            e["markets"] = mkt_map[t]

    prog.progress(1.0, text="Done!"); prog.empty()

    # ── Combine ────────────────────────────────────────────────────────────────
    combined = all_events + sports_events
    if not combined: return pd.DataFrame()

    df = pd.DataFrame(combined).drop_duplicates(subset=["event_ticker"])
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]  = df.get("series_ticker", pd.Series("", index=df.index)).fillna("")

    # Mark sports — either category=Sports OR fetched via a sport series ticker
    sport_event_tickers = {e.get("event_ticker") for e in sports_events}
    df["_is_sport"] = (df["category"] == "Sports") | df["event_ticker"].isin(sport_event_tickers)

    # Detect sport sub-category
    df["_sport"] = df.apply(
        lambda r: detect_sport(r.get("series_ticker",""), r.get("event_ticker","")) if r["_is_sport"] else "",
        axis=1
    )

    # Odds from nested markets
    def extract(row):
        mkts = row.get("markets") or []
        if not mkts: return "—","—",None
        m = mkts[0]
        yes = fmt_pct(m.get("yes_bid_dollars") or m.get("yes_bid"))
        no  = fmt_pct(m.get("no_bid_dollars")  or m.get("no_bid"))
        close = None
        for mk in mkts:
            d = safe_date(mk.get("close_time"))
            if d and (close is None or d < close): close = d
        return yes, no, close

    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = info[0]; df["_no"] = info[1]; df["_mkt_dt"] = info[2]

    def best_dt(row):
        for col in ["strike_date","close_time","end_date","expiration_time"]:
            d = safe_date(row.get(col))
            if d: return d
        return row.get("_mkt_dt")

    df["_sort_dt"]    = df.apply(best_dt, axis=1)
    df["_display_dt"] = df["_sort_dt"].apply(fmt_date)
    return df

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")
    search = st.text_input("🔍 Search", placeholder="team, market, keyword…")
    st.markdown("---")
    st.markdown("**📅 Date**")
    today     = date.today()
    date_mode = st.radio("Show", ["All dates","Today","Tomorrow","This week","Custom range"], index=0)
    d_start = d_end = None
    if date_mode == "Today":         d_start = d_end = today
    elif date_mode == "Tomorrow":    d_start = d_end = today + timedelta(days=1)
    elif date_mode == "This week":   d_start, d_end = today, today + timedelta(days=6)
    elif date_mode == "Custom range":
        d_start = st.date_input("From", value=today)
        d_end   = st.date_input("To",   value=today + timedelta(days=7))
    include_no_date = st.checkbox("Include events with no date", value=True)
    st.markdown("---")
    st.markdown("**↕️ Sort**")
    sort_by = st.radio("Order", ["Earliest first","Latest first","Default"], index=0)
    st.markdown("---")
    if st.button("🔄 Refresh"): fetch_all.clear(); st.rerun()
    st.caption("Cached 10 min.")

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")
with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials."); st.stop()

# ── Filter ─────────────────────────────────────────────────────────────────────
filtered = df.copy()
if date_mode != "All dates":
    def date_ok(row):
        if row["_is_sport"]: return True
        d = row["_sort_dt"]
        if d is None: return include_no_date
        try: return d_start <= d <= d_end
        except: return include_no_date
    filtered = filtered[filtered.apply(date_ok, axis=1)]

if search:
    s = search.lower()
    mask = (filtered["title"].str.lower().str.contains(s, na=False) |
            filtered["event_ticker"].str.lower().str.contains(s, na=False) |
            filtered["category"].str.lower().str.contains(s, na=False))
    filtered = filtered[mask]

if sort_by != "Default":
    asc     = sort_by == "Earliest first"
    has     = filtered["_sort_dt"].notna()
    dated   = filtered[has].copy()
    undated = filtered[~has].copy()
    dated["_sk"] = dated["_sort_dt"].apply(lambda d: str(d) if d else "9999")
    dated   = dated.sort_values("_sk", ascending=asc).drop(columns=["_sk"])
    filtered = pd.concat([dated, undated], ignore_index=True)

# ── Metrics ────────────────────────────────────────────────────────────────────
sport_count = int(df["_is_sport"].sum())
st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Card renderer ──────────────────────────────────────────────────────────────
def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets match your filters.</div>', unsafe_allow_html=True)
        return
    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker = str(row.get("event_ticker","")).upper()
            cat    = str(row.get("category","Other"))
            raw    = str(row.get("title","Unknown"))
            title  = raw.split(":")[-1].replace("Will the ","").split("?")[0].strip() or raw[:80]
            sport  = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon   = SPORT_ICON.get(sport, base_ic) if sport else base_ic
            label  = sport if sport and sport != "Other" else cat[:16]
            dt     = str(row.get("_display_dt","Open"))
            yes    = str(row.get("_yes","—"))
            no     = str(row.get("_no","—"))
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
        except Exception: continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── Sport tabs: sport → competition (series_ticker) ────────────────────────────
def render_sport_tabs(sdf):
    present = [s for _,s,_ in SPORTS if s in sdf["_sport"].values]
    if not present:
        render_cards(sdf); return

    labels   = ["🏟️ All"] + [f"{SPORT_ICON[s]} {s}" for s in present]
    tabs_top = st.tabs(labels)

    for i, tab in enumerate(tabs_top):
        with tab:
            if i == 0:
                render_cards(sdf)
            else:
                sport    = present[i-1]
                sport_df = sdf[sdf["_sport"] == sport].copy()

                # Group by series_ticker for competition sub-tabs
                series_present = sorted(sport_df["_series"].dropna().unique().tolist())
                series_present = [s for s in series_present if s]

                if len(series_present) <= 1:
                    render_cards(sport_df)
                else:
                    comp_labels = ["All"] + series_present
                    comp_tabs   = st.tabs(comp_labels)
                    for j, ctab in enumerate(comp_tabs):
                        with ctab:
                            if j == 0:
                                render_cards(sport_df)
                            else:
                                render_cards(sport_df[sport_df["_series"] == series_present[j-1]])

# ── Non-sport tag sub-tabs ─────────────────────────────────────────────────────
def render_tag_tabs(cat_df, cat):
    tags = CAT_TAGS.get(cat, [])
    if not tags:
        render_cards(cat_df); return
    tab_labels = ["All"] + tags
    ttabs = st.tabs(tab_labels)
    for i, ttab in enumerate(ttabs):
        with ttab:
            if i == 0:
                render_cards(cat_df)
            else:
                tag    = tags[i-1]
                tag_df = cat_df[
                    cat_df["title"].str.contains(tag, case=False, na=False, regex=False) |
                    cat_df["event_ticker"].str.contains(tag.replace(" ","").upper(), na=False)
                ]
                render_cards(tag_df)

# ── Main tabs ─────────────────────────────────────────────────────────────────
present_cats = ["All"] + [c for c in TOP_CATS if c in df["category"].values or (c == "Sports" and sport_count > 0)]
top_tabs = st.tabs(present_cats)

for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "All":
            render_cards(filtered)
        elif cat == "Sports":
            render_sport_tabs(filtered[filtered["_is_sport"]].copy())
        else:
            render_tag_tabs(filtered[filtered["category"] == cat].copy(), cat)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
