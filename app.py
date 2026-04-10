import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

# ====================== CSS ======================
CSS = """
<style>
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}

h1,h1 *{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}

.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;}
.market-card{background:#0a0a0a;border:1px solid #1c1c1c;border-radius:10px;padding:16px 18px;transition:border-color .15s,transform .15s;}
.market-card:hover{border-color:#00ff00;transform:translateY(-2px);}
.card-top{display:flex;justify-content:flex-start;align-items:center;margin-bottom:6px;}
.cat-pill{font-size:20px;font-weight:700;letter-spacing:.02em;text-transform:capitalize;padding:0;border:none;background:transparent;white-space:nowrap;color:#ffffff!important;}
.card-timing{display:flex;flex-direction:row;align-items:center;gap:4px;margin-bottom:8px;}
.date-text{font-size:11px;color:#ffffff;opacity:.6;}
.card-icon{font-size:20px;margin-bottom:4px;display:block;}
.card-title{font-size:14px;font-weight:600;color:#ffffff;line-height:1.45;margin-bottom:12px;min-height:52px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1c1c1c;padding-top:10px;}
.ticker-link{font-size:10px;color:#00ff00;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;text-decoration:none;opacity:.6;}
.ticker-link:hover{opacity:1;text-decoration:underline;}

.outcome-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;}
.outcome-label{font-size:11px;color:#ffffff;font-weight:500;flex:0 0 auto;min-width:80px;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.85;}
.outcome-chance{font-size:13px;font-weight:700;color:#ffffff;flex:0 0 auto;min-width:38px;text-align:right;}
.outcome-odds{display:flex;gap:6px;flex:1;justify-content:flex-end;}
.odds-yes{background:#001500;border:1px solid #00ff00;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{background:#150000;border:1px solid #ff2222;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#ffffff;text-transform:uppercase;letter-spacing:.08em;opacity:.5;}
.odds-price-yes{font-size:15px;font-weight:700;color:#00ff00;}
.odds-price-no{font-size:15px;font-weight:700;color:#ff2222;}
.empty-state{text-align:center;padding:80px 20px;color:#333;font-size:14px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

UTC = timezone.utc

# ── Category metadata ────────────────────────────────────────────────────────
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials","Crypto",
            "Companies","Entertainment","Climate and Weather","Science and Technology",
            "Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),"Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),"Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),"Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),"Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),"Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),"Social":("👥","pill-default"),
    "World":("🌐","pill-default"),"Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

# ==================== PASTE YOUR ORIGINAL DICTIONARIES HERE ====================
# Copy from your original app (43).py and paste them below

_SPORT_SERIES = {
    "Soccer": [ ... ],   # ← PASTE ALL YOUR DATA HERE
    "Basketball": [ ... ],
    # ... all other sports
}

SPORT_ICONS = { ... }      # ← Paste full
SOCCER_COMP = { ... }      # ← Paste full
SPORT_SUBTABS = { ... }    # ← Paste full
CAT_TAGS = { ... }         # ← Paste full if you use it

# Build SERIES_SPORT
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# ── Helpers ──────────────────────────────────────────────────────────────────
def safe_dt(val):
    try:
        if val is None or val == "": return None
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC)
    except: return None

def parse_game_date_from_ticker(event_ticker: str):
    import re
    from datetime import date as _date
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
              "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = event_ticker.split("-")
        if len(parts) < 2: return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m: return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        yr = 2000 + int(yy)
        mo = MONTHS.get(mon)
        if not mo: return None
        return _date(yr, mo, int(dd))
    except: return None

def fmt_date(d):
    try:
        if d is None: return ""
        if hasattr(d, 'hour'):
            try:
                import pytz
                eastern = pytz.timezone('US/Eastern')
            except ImportError:
                from zoneinfo import ZoneInfo
                eastern = ZoneInfo('America/New_York')
            if d.tzinfo:
                d = d.astimezone(eastern)
            tz_label = d.strftime('%Z') or "ET"
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} {tz_label}"
        return d.strftime("%b %d")
    except:
        return d.strftime("%b %d") if d else ""

# ── API ──────────────────────────────────────────────────────────────────────
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

def paginate(with_markets=False, category=None, max_pages=30):
    events, cursor = [], None
    for _ in range(max_pages):
        try:
            kw = {"limit":200,"status":"open"}
            if with_markets: kw["with_nested_markets"] = True
            if category: kw["category"] = category
            if cursor: kw["cursor"] = cursor
            resp = client.get_events(**kw).to_dict()
            batch = resp.get("events",[])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.05)
        except Exception as e:
            if "429" in str(e): time.sleep(3)
            else: break
    return events

@st.cache_data(ttl=1800)
def fetch_all():
    prog = st.progress(0, text="Loading markets…")
    all_ev = paginate(with_markets=True, max_pages=30)
    prog.progress(0.80, text=f"{len(all_ev)} events loaded…")
    if not all_ev:
        prog.empty(); return pd.DataFrame()

    df = pd.DataFrame(all_ev)
    df["category"] = df.get("category", pd.Series("Other")).fillna("Other").str.strip()
    df["_series"]  = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"]   = df["_series"].apply(get_sport)
    df["_is_sport"]= df["_sport"] != ""

    if "markets" not in df.columns:
        df["markets"] = [[] for _ in range(len(df))]
    df["markets"] = df["markets"].apply(lambda x: x if isinstance(x, list) else [])

    df["_soccer_comp"] = df.apply(
        lambda r: SOCCER_COMP.get(r["_series"],"Other") if r["_sport"]=="Soccer" else "", axis=1
    )

    # Use your original extract logic here
    def extract(row):
        mkts = row.get("markets", [])
        if not mkts:
            return None, None, None, None, None, "", []
        first_mk = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport = str(row.get("_sport", ""))
        game_date = parse_game_date_from_ticker(event_ticker)
        exp_dt = safe_dt(first_mk.get("expected_expiration_time"))
        kickoff_dt = exp_dt
        outcomes = []
        for mk in mkts:
            label = str(mk.get("yes_sub_title") or "").strip() or str(mk.get("ticker","")).split("-")[-1]
            yf = nf = None
            try:
                yd = mk.get("yes_bid_dollars") or mk.get("yes_bid")
                if yd is not None: yf = float(yd) / 100 if float(yd) > 1 else float(yd)
                nd = mk.get("no_bid_dollars") or mk.get("no_bid")
                if nd is not None: nf = float(nd) / 100 if float(nd) > 1 else float(nd)
            except: pass
            chance = f"{int(round(yf*100))}%" if yf is not None else "—"
            yes    = f"{int(round(yf*100))}¢" if yf is not None else "—"
            no     = f"{int(round(nf*100))}¢" if nf is not None else "—"
            outcomes.append((label[:35], chance, yes, no))
        return None, None, game_date, game_date, kickoff_dt, "", outcomes

    info = df.apply(extract, axis=1, result_type="expand")
    df["_mkt_dt"] = info[2]
    df["_kickoff_dt"] = info[4]
    df["_outcomes"] = info[6]
    df["_display_dt"] = df["_kickoff_dt"].apply(fmt_date)

    prog.progress(1.0); prog.empty()
    return df

# ── Automatic Infinite Scroll render_cards ───────────────────────────────────
def render_cards(data, tab_name="default"):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return

    BATCH_SIZE = 24
    state_key = f"visible_count_{tab_name}"

    if state_key not in st.session_state:
        st.session_state[state_key] = BATCH_SIZE

    visible = min(len(data), st.session_state[state_key])
    display_df = data.iloc[:visible]

    html = '<div class="card-grid">'
    for _, row in display_df.iterrows():
        try:
            ticker = str(row.get("event_ticker","")).upper()
            cat = str(row.get("category","Other"))
            title = str(row.get("title",""))[:90]
            sport = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label = sport[:16] if sport else cat[:16]
            dt = str(row.get("_display_dt","Open"))
            outcomes = row.get("_outcomes") or []

            series_lower = str(row.get("series_ticker","")).lower()
            ticker_lower = ticker.lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker_lower}" if series_lower else ""
            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'

            odds_html = ""
            if outcomes:
                for (olabel, ochance, oyes, ono) in outcomes[:5]:
                    safe_label = olabel[:30] if olabel else "—"
                    odds_html += f'''<div class="outcome-row">
                        <div class="outcome-label">{safe_label}</div>
                        <div class="outcome-chance">{ochance}</div>
                        <div class="outcome-odds">
                            <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{oyes}</div></div>
                            <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{ono}</div></div>
                        </div>
                    </div>'''
            else:
                odds_html = '<div class="outcome-row"><div class="outcome-label">—</div><div class="outcome-chance">—</div><div class="outcome-odds"><div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">—</div></div><div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">—</div></div></div></div>'

            dt_html = f'<div class="card-timing"><span class="date-text">{dt}</span></div>' if dt else ''

            html += f'''
            <div class="market-card">
                <div class="card-top"><span class="cat-pill {pill}">{label}</span></div>
                {dt_html}
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">{link_html}{odds_html}</div>
            </div>'''
        except:
            continue
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    # Automatic scroll loading
    if visible < len(data):
        st.markdown(f"""
        <script>
            function loadMore() {{
                var threshold = 400;
                if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - threshold) {{
                    var btn = document.querySelector('button[key="auto_load_{tab_name}"]');
                    if (btn) btn.click();
                }}
            }}
            window.addEventListener('scroll', loadMore);
            setTimeout(loadMore, 800);
        </script>
        """, unsafe_allow_html=True)

        if st.button("Load more", key=f"auto_load_{tab_name}", help=""):
            st.session_state[state_key] += BATCH_SIZE
            st.rerun()

# ── Main UI ──────────────────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

_c1, _c2, _c3 = st.columns([3, 1.4, 1])
with _c1:
    search = st.text_input("", placeholder="🔍  Search team, player, market…", label_visibility="collapsed")
with _c2:
    sort_by = st.selectbox("", ["Earliest first","Latest first","Default"], index=0, label_visibility="collapsed")
with _c3:
    if st.button("Refresh", use_container_width=True):
        fetch_all.clear()
        for key in list(st.session_state.keys()):
            if key.startswith("visible_count_") or key.startswith("auto_load_"):
                del st.session_state[key]
        st.rerun()

today = date.today()
_dfc1, _dfc2 = st.columns([2, 1])
with _dfc1:
    date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")
with _dfc2:
    include_no_date = st.toggle("Include undated", value=True)

with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials.")
    st.stop()

filtered = df.copy()

# Reset counts on filter change
filter_hash = hash((search or "", date_mode))
if "last_filter_hash" not in st.session_state or st.session_state.last_filter_hash != filter_hash:
    for key in list(st.session_state.keys()):
        if key.startswith("visible_count_"):
            del st.session_state[key]
    st.session_state.last_filter_hash = filter_hash

# ── Tabs ─────────────────────────────────────────────────────────────────────
present_cats = [""] + ["All"] + [c for c in TOP_CATS
    if (c=="Sports" and int(df["_is_sport"].sum()) > 0) or (c != "Sports" and c in df["category"].values)]

top_tabs = st.tabs(present_cats)

for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "":
            st.info("Select a category above to browse markets.")
        elif cat == "All":
            render_cards(filtered, tab_name="all")
        elif cat == "Sports":
            sdf = filtered[filtered["_is_sport"]].copy()
            sports_present = [s for s in _SPORT_SERIES.keys() if s in sdf["_sport"].values]

            nav_col, card_col = st.columns([1, 4])
            with nav_col:
                if "sel_sport" not in st.session_state:
                    st.session_state.sel_sport = "All sports"

                for item in ["All sports"] + sports_present:
                    cnt = len(sdf) if item == "All sports" else int((sdf["_sport"]==item).sum())
                    is_sel = st.session_state.sel_sport == item
                    color = "#00ff00" if is_sel else "#ffffff"
                    weight = "bold" if is_sel else "normal"
                    st.markdown(f"<div style='color:{color};font-weight:{weight};padding:6px 0;cursor:pointer;'>{item} ({cnt})</div>", unsafe_allow_html=True)
                    if st.button(item, key=f"sp_{item.replace(' ','_')}"):
                        st.session_state.sel_sport = item
                        st.rerun()

            with card_col:
                s = st.session_state.get("sel_sport", "All sports")
                view = sdf if s == "All sports" else sdf[sdf["_sport"] == s].copy()
                render_cards(view, tab_name=f"sports_{s.replace(' ', '_')}")
        else:
            cat_data = filtered[filtered["category"] == cat].copy()
            render_cards(cat_data, tab_name=f"cat_{cat.replace(' ', '_')}")

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 30 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
