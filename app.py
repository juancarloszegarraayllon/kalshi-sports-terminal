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
.cat-pill { font-size: 10px; font-weight: 500; letter-spacing: .08em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; border: 1px solid; white-space: nowrap; }
.pill-sports       { background: #1a2e1a; color: #4ade80; border-color: #166534; }
.pill-elections    { background: #2e1a1e; color: #f472b6; border-color: #9d174d; }
.pill-politics     { background: #1e1a2e; color: #818cf8; border-color: #3730a3; }
.pill-economics    { background: #2e2a1a; color: #fbbf24; border-color: #92400e; }
.pill-financials   { background: #2e2a1a; color: #fb923c; border-color: #9a3412; }
.pill-crypto       { background: #1e2a2e; color: #67e8f9; border-color: #0e7490; }
.pill-companies    { background: #2e1e2e; color: #d8b4fe; border-color: #7e22ce; }
.pill-entertainment{ background: #2e1e1a; color: #fdba74; border-color: #c2410c; }
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
.card-title { font-size: 14px; font-weight: 500; color: #e2e8f0; line-height: 1.45; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; min-height: 60px; }
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
.stTabs [data-baseweb="tab"] { background: transparent; color: #4b5563; border: none; font-size: 12px; letter-spacing: .04em; padding: 8px 12px; }
.stTabs [aria-selected="true"] { background: #1e1e32 !important; color: #a5b4fc !important; border-radius: 6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ── Exact Kalshi structure from API debug ──────────────────────────────────────

# Top-level category order (matches kalshi.com nav)
TOP_CATS = [
    "Sports", "Elections", "Politics", "Economics", "Financials",
    "Crypto", "Companies", "Entertainment", "Climate and Weather",
    "Science and Technology", "Health", "Social", "World",
    "Transportation", "Mentions",
]

CAT_META = {
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

# Tags per category (from /search/tags_by_categories)
CAT_TAGS = {
    "Climate and Weather":    ["Daily temperature","Snow and rain","Climate change","Natural disasters","Hurricanes","Hourly temperature"],
    "Companies":              ["IPOs","Product launches","KPIs","Elon Musk","CEOs","Layoffs"],
    "Crypto":                 ["BTC","ETH","SOL","DOGE","BNB","HYPE","XRP","15 min","Hourly","Pre-Market"],
    "Economics":              ["Growth","Inflation","Oil and energy","Jobs & Economy","Fed","GDP","Global Central Banks","Housing"],
    "Elections":              ["US Elections","Primaries","House","International elections"],
    "Entertainment":          ["Music","Television","Awards","Movies","Music charts","Oscars","Video games","Rotten Tomatoes"],
    "Financials":             ["Agriculture","Oil & Gas","Metals","S&P","Nasdaq","Daily","Treasuries","EUR/USD","USD/JPY"],
    "Health":                 ["Diseases"],
    "Mentions":               ["Earnings","Politicians","Sports"],
    "Politics":               ["Trump","Congress","International","SCOTUS & courts","Recurring","Local","Iran"],
    "Science and Technology": ["AI","Energy","Medicine","Space"],
}

# Sports: ordered list of (icon, name, competitions)
SPORTS_STRUCTURE = [
    ("🏀", "Basketball", ["Pro Basketball (M)","College Basketball (M)","Euroleague","Adriatic ABA League","Spain Liga ACB","Germany BBL","Italy Serie A","Turkey BSL","Russia VTB United League","Japan B League","LNB Elite","Pro Basketball (W)","Liga Nacional de Basquetbol","Chinese Basketball Association","Israeli Super League"]),
    ("⚾", "Baseball",   ["Pro Baseball","College Baseball","Japan NPB","Korea KBO"]),
    ("🎾", "Tennis",     ["ATP Monte Carlo","ATP French Open","WTA French Open","WTA Linz","ATP Challenger Madrid","ATP Challenger Monza","ATP Challenger Wuning","WTA 125K Madrid","ATP"]),
    ("⚽", "Soccer",     ["EPL","La Liga","Serie A","Bundesliga","Ligue 1","Champions League","Europa League","Conference League","MLS","Liga MX","Brasileiro Serie A","Eredivisie","Liga Portugal","Belgian Pro League","Allsvenskan","Danish Superliga","EFL Championship","Super Lig","Swiss Super League","Scotland Premiership","Korea K League 1","Japan J1 League","Chinese Super League","AFC Champions","CONCACAF Champions Cup","CONMEBOL Libertadores","CONMEBOL Sudamericana","Copa del Rey","Coppa Italia","DFB Pokal","FA Cup","FIFA World Cup","Champions League Womens","Bundesliga 2","La Liga 2","Serie B","USL Championship","Uruguay Primera Division","Chile Liga de Primera","Ecuador LigaPro","Venezuela Liga FUTVE","Colombia Liga DIMAYOR","Argentina Primera Division","Australia A League","Thai League 1","Egypt Premier League","Croatian HNL","Ekstraklasa","Greece Super League","KNVB","AFC Champions League","APF Division de Honor","Baller League","Liga 1 Peru"]),
    ("🏒", "Hockey",     ["Pro Hockey","College Hockey","AHL","Finland Liiga","Czech Extraliga","Germany DEL","Switzerland National League","KHL","SHL"]),
    ("⛳", "Golf",       ["The Masters","Ryder Cup"]),
    ("🥊", "MMA",        ["UFC"]),
    ("🏏", "Cricket",    ["IPL","PSL","T20 International"]),
    ("🏈", "Football",   ["Pro Football","College Football","UFL"]),
    ("🎮", "Esports",    ["CS2","League of Legends","Valorant","Dota 2","Overwatch","Rainbow Six Siege"]),
    ("🏎️","Motorsport",  ["F1","NASCAR Cup Series","NASCAR O'Reilly Auto Parts Series","NASCAR Truck Series","IndyCar","MotoGP"]),
    ("🏉", "Aussie Rules",["AFL"]),
    ("🥊", "Boxing",     ["Boxing"]),
    ("🥍", "Lacrosse",   ["College Lacrosse"]),
    ("🏉", "Rugby",      ["National Rugby League","France Top 14","Gallagher Premiership","Super League Rugby"]),
    ("🎯", "Darts",      ["Premier League Darts"]),
    ("♟️", "Chess",      []),
    ("🏟️","Other",       ["SailGP"]),
]

SPORT_ICON = {s: ic for ic, s, _ in SPORTS_STRUCTURE}
SPORT_COMPS = {s: comps for _, s, comps in SPORTS_STRUCTURE}

# Map competition name keywords → sport
COMP_TO_SPORT = {}
for _, sport, comps in SPORTS_STRUCTURE:
    for c in comps:
        COMP_TO_SPORT[c.lower()] = sport

# Series ticker prefix → sport (from debug output)
TICKER_TO_SPORT = {}
TICKER_PREFIXES = {
    "Basketball": ["NBA","WNBA","NCAAB","KXNBA","KXWNBA","KXNCAAB","KXNBASEATTLE","KXNBATEAM","KXSONICS","KXSPORTSOWNERLBJ"],
    "Baseball":   ["MLB","NCAAB","KXMLB"],
    "Tennis":     ["ATP","WTA","KXATP","KXWTA"],
    "Soccer":     ["EPL","MLS","UEFA","FIFA","KXEPL","KXMLS","KXUEFA","KXFIFA","KXSOC","SOC"],
    "Hockey":     ["NHL","AHL","KXNHL","KXAHL"],
    "Golf":       ["PGA","KXPGA","KXGOLF","GOLF","MASTERS","KXMASTERS"],
    "MMA":        ["UFC","MMA","KXUFC","KXMMA"],
    "Cricket":    ["IPL","PSL","KXIPL","KXPSL","KXCRICKET","CRICKET","BBL"],
    "Football":   ["NFL","NCAAF","KXNFL","KXNCAAF","UFL","KXUFL"],
    "Esports":    ["CS2","LOL","DOTA","VAL","OW","R6","KXESPORT","ESPORT"],
    "Motorsport": ["F1","NASCAR","KXF1","KXNASCAR","INDYCAR","MOTOGP","KXMOTOGP"],
    "Aussie Rules":["AFL","KXAFL"],
    "Boxing":     ["BOX","KXBOX"],
    "Lacrosse":   ["LAX","NLL","PLL","KXLAX"],
    "Rugby":      ["NRL","RUGBY","KXNRL","KXRUGBY","KXSUPER"],
    "Darts":      ["DART","PDC","KXDART"],
    "Chess":      ["CHESS","FIDE","KXCHESS"],
}

def detect_sport(ticker, series=""):
    t = (ticker + " " + series).upper()
    for sport, prefixes in TICKER_PREFIXES.items():
        if any(p in t for p in prefixes):
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
    except Exception:
        return None

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
        st.error(f"❌ Connection failed: {e}"); st.stop()

client = get_client()

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
    all_ev = paginate(with_markets=False)
    prog.progress(0.5, text=f"{len(all_ev)} events. Fetching sports odds…")
    sports_ev = paginate(with_markets=True, category="Sports")
    prog.empty()

    mkt_map = {e["event_ticker"]: e.get("markets",[]) for e in sports_ev if e.get("markets")}
    for e in all_ev:
        if e.get("event_ticker") in mkt_map:
            e["markets"] = mkt_map[e["event_ticker"]]

    if not all_ev: return pd.DataFrame()
    df = pd.DataFrame(all_ev).drop_duplicates(subset=["event_ticker"])
    df["category"]  = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]   = df.get("series_ticker", pd.Series("", index=df.index)).fillna("")
    df["_is_sport"] = df["category"] == "Sports"

    # Detect sport sub-category
    df["_sport"] = df.apply(
        lambda r: detect_sport(str(r.get("event_ticker","")), str(r.get("series_ticker",""))) if r["_is_sport"] else "",
        axis=1
    )

    # Detect non-sport tag (sub-category) from series_ticker
    def detect_tag(row):
        if row["_is_sport"]: return ""
        cat  = row["category"]
        tags = CAT_TAGS.get(cat, [])
        ser  = str(row.get("series_ticker","")).upper()
        tit  = str(row.get("title","")).lower()
        # Simple keyword match against tags
        for tag in tags:
            if tag.lower().replace(" ","") in ser.lower().replace(" ","") or \
               tag.lower() in tit:
                return tag
        return ""
    df["_tag"] = df.apply(detect_tag, axis=1)

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
            ticker  = str(row.get("event_ticker","")).upper()
            cat     = str(row.get("category","Other"))
            raw     = str(row.get("title","Unknown"))
            title   = raw.split(":")[-1].replace("Will the ","").split("?")[0].strip() or raw[:80]
            sport   = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon    = SPORT_ICON.get(sport, base_ic) if sport else base_ic
            label   = sport if sport and sport != "Other" else cat[:16]
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

# ── Sub-tab renderer for sports ────────────────────────────────────────────────
def render_sport_tabs(sdf):
    """Sports tab: sub-tabs by sport, then by competition."""
    present_sports = [s for _, s, _ in SPORTS_STRUCTURE if s in sdf["_sport"].values]
    if not present_sports:
        render_cards(sdf); return

    sport_labels = ["🏟️ All"] + [f"{SPORT_ICON[s]} {s}" for s in present_sports]
    sport_tabs   = st.tabs(sport_labels)

    for i, stab in enumerate(sport_tabs):
        with stab:
            if i == 0:
                render_cards(sdf)
            else:
                sport_name = present_sports[i-1]
                sport_df   = sdf[sdf["_sport"] == sport_name].copy()
                comps      = SPORT_COMPS.get(sport_name, [])

                # Find which competitions are present by matching series_ticker
                def match_comp(series, comp):
                    s = str(series).upper()
                    c = comp.upper().replace(" ","")
                    # Try direct keyword match
                    for word in comp.split():
                        if len(word) > 3 and word.upper() in s:
                            return True
                    return False

                present_comps = []
                for comp in comps:
                    if sport_df["_series"].apply(lambda s: match_comp(s, comp)).any():
                        present_comps.append(comp)

                if not present_comps:
                    render_cards(sport_df)
                else:
                    comp_labels = ["All"] + present_comps
                    comp_tabs   = st.tabs(comp_labels)
                    for j, ctab in enumerate(comp_tabs):
                        with ctab:
                            if j == 0:
                                render_cards(sport_df)
                            else:
                                comp = present_comps[j-1]
                                comp_df = sport_df[sport_df["_series"].apply(lambda s: match_comp(s, comp))]
                                render_cards(comp_df)

# ── Tag sub-tabs for non-sport categories ──────────────────────────────────────
def render_tag_tabs(cat_df, cat):
    tags = CAT_TAGS.get(cat, [])
    if not tags:
        render_cards(cat_df); return

    present_tags = ["All"] + [t for t in tags if cat_df["_tag"].str.contains(t, case=False, na=False, regex=False).any() or True]
    # Simpler: just show all tags as sub-tabs, empty ones show empty state
    tag_tabs = st.tabs(["All"] + tags)
    for i, ttab in enumerate(tag_tabs):
        with ttab:
            if i == 0:
                render_cards(cat_df)
            else:
                tag = tags[i-1]
                tag_df = cat_df[cat_df["_tag"] == tag]
                if tag_df.empty:
                    # Fallback: keyword search in title
                    tag_df = cat_df[cat_df["title"].str.contains(tag, case=False, na=False, regex=False)]
                render_cards(tag_df)

# ── Main tabs (top-level categories) ──────────────────────────────────────────
present_cats = ["All"] + [c for c in TOP_CATS if c in df["category"].values]
top_tabs = st.tabs(present_cats)

for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "All":
            render_cards(filtered)
        elif cat == "Sports":
            sdf = filtered[filtered["_is_sport"]].copy()
            render_sport_tabs(sdf)
        else:
            cat_df = filtered[filtered["category"] == cat].copy()
            render_tag_tabs(cat_df, cat)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
