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
section[data-testid="stSidebar"] .stSelectbox > div { background: #1a1a2e !important; }
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
.pill-sports       { background: #1a2e1a; color: #4ade80; border-color: #166534; }
.pill-elections    { background: #2e1a1e; color: #f472b6; border-color: #9d174d; }
.pill-politics     { background: #1e1a2e; color: #818cf8; border-color: #3730a3; }
.pill-economics    { background: #2e2a1a; color: #fbbf24; border-color: #92400e; }
.pill-financials   { background: #2e2a1a; color: #fbbf24; border-color: #92400e; }
.pill-crypto       { background: #1e2a2e; color: #67e8f9; border-color: #0e7490; }
.pill-companies    { background: #2e1e2e; color: #d8b4fe; border-color: #7e22ce; }
.pill-entertainment{ background: #2e1e1a; color: #fb923c; border-color: #9a3412; }
.pill-climate      { background: #1a2e2e; color: #22d3ee; border-color: #164e63; }
.pill-science      { background: #1e2e1a; color: #86efac; border-color: #14532d; }
.pill-health       { background: #2e1a2e; color: #e879f9; border-color: #701a75; }
.pill-social       { background: #2e1e2a; color: #f9a8d4; border-color: #9d174d; }
.pill-world        { background: #1a1e2e; color: #93c5fd; border-color: #1e40af; }
.pill-transport    { background: #2e2e1a; color: #d9f99d; border-color: #3f6212; }
.pill-mentions     { background: #1e2e2e; color: #5eead4; border-color: #0f766e; }
.pill-default      { background: #1e1e32; color: #94a3b8; border-color: #2d2d55; }
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
.stTabs [data-baseweb="tab-list"] { background: #0f0f1a; border-bottom: 1px solid #1e1e32; gap: 2px; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #4b5563; border: none; font-size: 12px; letter-spacing: .04em; padding: 8px 14px; }
.stTabs [aria-selected="true"] { background: #1e1e32 !important; color: #a5b4fc !important; border-radius: 6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

UTC      = timezone.utc
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

# ── Kalshi category → display structure (mirrors kalshi.com nav) ───────────────
# Top-level categories exactly as returned by the API, with icon + pill class
CATEGORY_META = {
    "Sports":                 ("🏟️", "pill-sports"),
    "Elections":              ("🗳️", "pill-elections"),
    "Politics":               ("🏛️", "pill-politics"),
    "Economics":              ("📈", "pill-economics"),
    "Financials":             ("💰", "pill-financials"),
    "Crypto":                 ("₿",  "pill-crypto"),
    "Companies":              ("🏢", "pill-companies"),
    "Entertainment":          ("🎬", "pill-entertainment"),
    "Climate and Weather":    ("🌍", "pill-climate"),
    "Science and Technology": ("🔬", "pill-science"),
    "Health":                 ("🏥", "pill-health"),
    "Social":                 ("👥", "pill-social"),
    "World":                  ("🌐", "pill-world"),
    "Transportation":         ("✈️", "pill-transport"),
    "Mentions":               ("💬", "pill-mentions"),
}

# Sports sub-categories (from Kalshi's /search/filters_by_sport)
SPORT_SUBS = [
    ("🏀", "Basketball"), ("⚾", "Baseball"), ("🎾", "Tennis"),
    ("⚽", "Soccer"),     ("🏒", "Hockey"),   ("⛳", "Golf"),
    ("🥊", "MMA"),        ("🏏", "Cricket"),  ("🏈", "Football"),
    ("🎮", "Esports"),    ("🏎️", "Motorsport"),("🥊", "Boxing"),
    ("🏉", "Rugby"),      ("🥍", "Lacrosse"), ("🎯", "Darts"),
    ("♟️", "Chess"),      ("🏉", "Aussie Rules"),
]

# Detect sport sub-category from ticker
def detect_sport(ticker, title=""):
    t = ticker.upper()
    ti = title.upper()

    # Use series_ticker prefix — most reliable signal
    # Kalshi formats: KXNBA-..., KXMLB-..., KXNHL-..., KXNFL-...
    # Check for exact word-boundary prefixes first to avoid false matches

    # Basketball
    if any(t.startswith(x) or ("-"+x+"-") in t or t.startswith("KX"+x)
           for x in ["NBA","NCAAB","WNBA"]):                return "Basketball"
    if "BASKETBALL" in t or "BASKETBALL" in ti:             return "Basketball"

    # Baseball
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["MLB","NCAASB"]):                      return "Baseball"
    if "BASEBALL" in t or "BASEBALL" in ti:                 return "Baseball"

    # Hockey
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["NHL","AHL"]):                         return "Hockey"
    if "HOCKEY" in t or "HOCKEY" in ti:                     return "Hockey"

    # American Football
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["NFL","NCAAF","XFL"]):                 return "Football"
    if "FOOTBALL" in t or "SUPERBOWL" in t:                 return "Football"

    # Soccer — use full word SOCCER or known league prefixes, NOT "SOC" alone
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["MLS","EPL","UCL","LALIGA","SERIEA","BUNDES","LIGUE1","CONCACAF"]):
                                                            return "Soccer"
    if "SOCCER" in t or "SOCCER" in ti:                     return "Soccer"
    if any(x in t for x in ["UEFA","FIFA","CHAMPIONS-LEAGUE","PREMIER-LEAGUE"]): return "Soccer"
    # Common soccer team name patterns in tickers
    if any(x in t for x in ["TIGRES","SEATTLE-SOUNDERS","LAFC","ATLUTD","NYCFC",
                              "INTER-MIAMI","REALMADRID","BARCELONA","CHELSEA",
                              "ARSENAL","MANCITY","LIVERPOOL","JUVENTUS","ACMILAN"]):
                                                            return "Soccer"

    # Tennis
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["ATP","WTA","ITF","AUSOPEN","FRENCHOPEN","WIMBLEDON","USOPEN-TEN"]):
                                                            return "Tennis"
    if "TENNIS" in t or "TENNIS" in ti:                     return "Tennis"

    # Golf
    if any(t.startswith(x) or t.startswith("KX"+x)
           for x in ["PGA","LPGA","DPWT","MASTERS","USOPEN-GOLF","THEOPEN"]):
                                                            return "Golf"
    if "GOLF" in t or "GOLF" in ti:                         return "Golf"

    # MMA / UFC
    if any(x in t for x in ["UFC","BELLATOR","ONE-FC","PFL"]):  return "MMA"
    if "MMA" in t or "MMA" in ti:                           return "MMA"

    # Cricket
    if any(x in t for x in ["IPL","BBL","CPL","PSL","CRICKET","TEST-MATCH"]):
                                                            return "Cricket"

    # Motorsport
    if any(x in t for x in ["FORMULA1","F1-","NASCAR","INDYCAR","MOTOGP","RALLYE"]):
                                                            return "Motorsport"

    # Boxing
    if "BOXING" in t or "BOXING" in ti:                     return "Boxing"

    # Rugby
    if any(x in t for x in ["RUGBY","NRL","SUPERLEAGUE","SIX-NATIONS","WORLDRUGBY"]):
                                                            return "Rugby"

    # Lacrosse
    if any(x in t for x in ["NLL","PLL","LACROSSE"]):       return "Lacrosse"

    # Darts
    if any(x in t for x in ["PDC","DARTSLIVE","DARTS"]):    return "Darts"

    # Chess
    if any(x in t for x in ["FIDE","CHESS"]):               return "Chess"

    # Aussie Rules
    if any(x in t for x in ["AFL","AFLW"]):                 return "Aussie Rules"

    # Esports
    if any(x in t for x in ["ESPORT","CS2","CSGO","DOTA","LEAGUE-OF-LEGENDS",
                              "VALORANT","OVERWATCH","ROCKETLEAGUE"]):
                                                            return "Esports"

    return "Other"

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_date(val):
    try:
        if val is None or val == "": return None
        if isinstance(val, date) and not isinstance(val, pd.Timestamp): return val
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC).date()
    except Exception:
        return None

def fmt_date(d):
    try:
        return d.strftime("%b %d, %Y") if d else "Open"
    except Exception:
        return "Open"

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f * 100)) if f <= 1.0 else int(round(f))}%"
    except Exception:
        return "—"

# ── API client ─────────────────────────────────────────────────────────────────
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
        st.error(f"❌ Connection failed: {e}"); st.stop()

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
    prog = st.progress(0, text="Fetching all events…")
    # Pass 1: all events, fast
    all_ev = paginate(with_markets=False)
    prog.progress(0.5, text=f"{len(all_ev)} events. Fetching sports odds…")
    # Pass 2: sports with markets for odds
    sports_ev = paginate(with_markets=True, category="Sports")
    prog.empty()

    mkt_map = {e["event_ticker"]: e.get("markets", []) for e in sports_ev if e.get("markets")}
    for e in all_ev:
        if e.get("event_ticker") in mkt_map:
            e["markets"] = mkt_map[e["event_ticker"]]

    if not all_ev: return pd.DataFrame()

    df = pd.DataFrame(all_ev).drop_duplicates(subset=["event_ticker"])
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_is_sport"] = df["category"] == "Sports"

    # Odds from nested markets
    def extract(row):
        mkts = row.get("markets") or []
        if not mkts: return "—", "—", None
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
        for col in ["strike_date", "close_time", "end_date", "expiration_time"]:
            d = safe_date(row.get(col))
            if d: return d
        return row.get("_mkt_dt")

    df["_sort_dt"]    = df.apply(best_dt, axis=1)
    df["_display_dt"] = df["_sort_dt"].apply(fmt_date)
    df["_sport_sub"]  = df.apply(lambda r: detect_sport(str(r.get("event_ticker","")), str(r.get("title",""))) if r["_is_sport"] else "", axis=1)
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
    if date_mode == "Today":          d_start = d_end = today
    elif date_mode == "Tomorrow":     d_start = d_end = today + timedelta(days=1)
    elif date_mode == "This week":    d_start, d_end = today, today + timedelta(days=6)
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
        if row["_is_sport"]: return True   # sports always show
        d = row["_sort_dt"]
        if d is None: return include_no_date
        try: return d_start <= d <= d_end
        except Exception: return include_no_date
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
            _, pill = CATEGORY_META.get(cat, ("📊", "pill-default"))
            dt     = str(row.get("_display_dt","Open"))
            yes    = str(row.get("_yes","—"))
            no     = str(row.get("_no","—"))
            sub    = str(row.get("_sport_sub",""))
            label  = sub if sub and sub != "Other" else cat[:14]
            icon_map = {"Basketball":"🏀","Baseball":"⚾","Hockey":"🏒","Football":"🏈",
                        "Soccer":"⚽","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
                        "Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉","Darts":"🎯",
                        "Chess":"♟️","Aussie Rules":"🏉","Esports":"🎮"}
            base_icon = CATEGORY_META.get(cat, ("📊",""))[0]
            icon = icon_map.get(sub, base_icon) if sub else base_icon

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

# ── Navigation — mirrors Kalshi.com structure ──────────────────────────────────
# Top-level tabs in same order as Kalshi's website
TOP_TABS = ["All"] + [c for c in CATEGORY_META.keys() if c in df["category"].unique()]

tabs = st.tabs(TOP_TABS)
for i, tab in enumerate(tabs):
    with tab:
        cat = TOP_TABS[i]

        if cat == "All":
            render_cards(filtered)

        elif cat == "Sports":
            # Sports → sub-tabs by sport (Basketball, Soccer, Tennis…)
            sdf = filtered[filtered["_is_sport"]].copy()
            present_subs  = [s for _, s in SPORT_SUBS if s in sdf["_sport_sub"].values]
            has_other     = "Other" in sdf["_sport_sub"].values
            sub_names     = present_subs + (["Other"] if has_other else [])
            sub_icons     = {s: ic for ic, s in SPORT_SUBS}
            sub_labels    = ["All Sports"] + [f"{sub_icons.get(s,'🏟️')} {s}" for s in sub_names]

            sub_tabs = st.tabs(sub_labels)
            for j, stab in enumerate(sub_tabs):
                with stab:
                    if j == 0:
                        render_cards(sdf)
                    else:
                        render_cards(sdf[sdf["_sport_sub"] == sub_names[j-1]])

        elif cat == "Elections":
            # Elections — show with a series_ticker sub-filter if possible
            edf = filtered[filtered["category"] == "Elections"]
            # Group by series_ticker prefix for sub-categories
            edf = edf.copy()
            edf["_series"] = edf["series_ticker"].fillna("Other") if "series_ticker" in edf.columns else "Other"
            unique_series = sorted(edf["_series"].unique().tolist())[:8]  # cap at 8
            if len(unique_series) > 1:
                sub_labels = ["All Elections"] + unique_series
                sub_tabs   = st.tabs(sub_labels)
                for j, stab in enumerate(sub_tabs):
                    with stab:
                        if j == 0: render_cards(edf)
                        else:      render_cards(edf[edf["_series"] == unique_series[j-1]])
            else:
                render_cards(edf)

        else:
            render_cards(filtered[filtered["category"] == cat])

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
