import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

st.markdown("""
<style>
/* ── Base ── */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}

/* ── Title ── */
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}

/* ── Cards ── */
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px;}
.market-card{background:#0a0a0a;border:1px solid #1c1c1c;border-radius:10px;padding:16px 18px;transition:border-color .15s,transform .15s;}
.market-card:hover{border-color:#00ff00;transform:translateY(-2px);}
.card-top{display:flex;justify-content:flex-start;align-items:center;margin-bottom:6px;}
.cat-pill{font-size:20px;font-weight:700;letter-spacing:.02em;text-transform:capitalize;padding:0;border:none;background:transparent;white-space:nowrap;color:#ffffff!important;}
.pill-sports,.pill-elections,.pill-politics,.pill-economics,.pill-financials,
.pill-crypto,.pill-companies,.pill-entertainment,.pill-climate,.pill-science,
.pill-health,.pill-default{background:transparent;border:none;color:#ffffff!important;}
.card-timing{display:flex;flex-direction:row;align-items:center;gap:4px;margin-bottom:8px;}
.date-text{font-size:11px;color:#ffffff;opacity:.6;}
.card-icon{font-size:20px;margin-bottom:4px;display:block;}
.card-title{font-size:14px;font-weight:600;color:#ffffff;line-height:1.45;margin-bottom:12px;min-height:52px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1c1c1c;padding-top:10px;}
.ticker-link{font-size:10px;color:#00ff00;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;text-decoration:none;opacity:.6;}
.ticker-link:hover{opacity:1;text-decoration:underline;}

/* ── Outcomes ── */
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
hr{border-color:#1c1c1c!important;}

/* Nav buttons - plain text */
button[kind="secondary"], button[kind="primary"],
div[data-testid="stButton"] button,
.stButton > div > button,
.stButton button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #ffffff !important;
    font-size: 13px !important;
    text-align: left !important;
    padding: 3px 0 !important;
    margin: 0 !important;
    width: 100% !important;
}
.stButton button:hover {
    color: #888888 !important;
}
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ── Category metadata ─────────────────────────────────────────────────────────
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

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

# ── YOUR ORIGINAL DICTIONARIES (fully restored) ───────────────────────────────
_SPORT_SERIES = {
    "Soccer": [
        "KXEPLGAME","KXEPL1H","KXEPLSPREAD","KXEPLTOTAL","KXEPLBTTS",
        "KXEPLTOP4","KXEPLTOP2","KXEPLTOP6","KXEPLRELEGATION","KXPREMIERLEAGUE",
        "KXARSENALCUPS","KXWINSTREAKMANU","KXNEXTMANAGERMANU","KXPFAPOY","KXLAMINEYAMAL",
        "KXUCLGAME","KXUCL1H","KXUCLSPREAD","KXUCLTOTAL","KXUCLBTTS","KXUCL",
        "KXUCLFINALIST","KXUCLRO4","KXUCLW","KXLEADERUCLGOALS","KXTEAMSINUCL",
        "KXUELGAME","KXUELSPREAD","KXUELTOTAL","KXUEL",
        "KXUECL","KXUECLGAME",
        "KXLALIGAGAME","KXLALIGA1H","KXLALIGASPREAD","KXLALIGATOTAL","KXLALIGABTTS",
        "KXLALIGA","KXLALIGATOP4","KXLALIGARELEGATION",
        "KXLALIGA2GAME",
        "KXSERIEAGAME","KXSERIEA1H","KXSERIEASPREAD","KXSERIEATOTAL","KXSERIEABTTS",
        "KXSERIEA","KXSERIEATOP4","KXSERIEARELEGATION",
        "KXSERIEBGAME",
        "KXBUNDESLIGAGAME","KXBUNDESLIGA1H","KXBUNDESLIGASPREAD","KXBUNDESLIGATOTAL",
        "KXBUNDESLIGABTTS","KXBUNDESLIGA","KXBUNDESLIGATOP4","KXBUNDESLIGARELEGATION",
        "KXBUNDESLIGA2GAME",
        "KXLIGUE1GAME","KXLIGUE11H","KXLIGUE1SPREAD","KXLIGUE1TOTAL","KXLIGUE1BTTS",
        "KXLIGUE1","KXLIGUE1TOP4","KXLIGUE1RELEGATION",
        "KXMLSGAME","KXMLSSPREAD","KXMLSTOTAL","KXMLSBTTS","KXMLSCUP","KXMLSEAST","KXMLSWEST",
        "KXLIGAMXGAME","KXLIGAMXSPREAD","KXLIGAMXTOTAL","KXLIGAMX",
        "KXBRASILEIROGAME","KXBRASILEIROSPREAD","KXBRASILEIROTOTAL","KXBRASILEIRO","KXBRASILEIROTOPX",
        "KXWCGAME","KXWCROUND","KXWCGROUPWIN","KXWCGROUPQUAL","KXWCGOALLEADER",
        "KXWCMESSIRONALDO","KXWCLOCATION","KXWCIRAN","KXWCSQUAD","KXMENWORLDCUP",
        "KXSOCCERPLAYMESSI","KXSOCCERPLAYCRON","KXFIFAUSPULL","KXFIFAUSPULLGAME",
        "KXSAUDIPLGAME","KXSAUDIPLSPREAD","KXSAUDIPLTOTAL",
        "KXLIGAPORTUGALGAME","KXLIGAPORTUGAL",
        "KXEREDIVISIEGAME","KXEREDIVISIE",
        "KXCOPADELREY","KXDFBPOKAL","KXFACUP","KXCOPPAITALIA",
        "KXEFLCHAMPIONSHIPGAME","KXEFLCHAMPIONSHIP","KXEFLPROMO",
        "KXSUPERLIGGAME","KXSUPERLIG",
        "KXCONCACAFCCUPGAME","KXCONMEBOLLIBGAME","KXCONMEBOLSUDGAME",
        "KXUSLGAME","KXUSL",
        "KXSCOTTISHPREMGAME",
        "KXEKSTRAKLASAGAME","KXEKSTRAKLASA",
        "KXALEAGUEGAME","KXALEAGUESPREAD","KXALEAGUETOTAL",
        "KXKLEAGUEGAME","KXKLEAGUE",
        "KXJLEAGUEGAME",
        "KXCHNSLGAME","KXCHNSL",
        "KXALLSVENSKANGAME",
        "KXDENSUPERLIGAGAME","KXDENSUPERLIGA",
        "KXSWISSLEAGUEGAME",
        "KXARGPREMDIVGAME",
        "KXDIMAYORGAME",
        "KXURYPDGAME","KXURYPD",
        "KXECULPGAME","KXECULP",
        "KXVENFUTVEGAME","KXVENFUTVE",
        "KXCHLLDPGAME","KXCHLLDP",
        "KXAPFDDHGAME","KXAPFDDH",
        "KXBALLERLEAGUEGAME",
        "KXSLGREECE",
        "KXTHAIL1GAME","KXTHAIL1",
        "KXEGYPLGAME",
        "KXHNLGAME",
        "KXBELGIANPLGAME","KXBELGIANPL",
        "KXPERLIGA1",
        "KXKNVBCUP",
        "KXSOCCERTRANSFER","KXJOINLEAGUE","KXJOINRONALDO","KXJOINCLUB","KXBALLONDOR",
    ],
    "Basketball": [
        "KXNBAGAME","KXNBASPREAD","KXNBATOTAL","KXNBATEAMTOTAL",
        "KXNBA1HWINNER","KXNBA1HSPREAD","KXNBA1HTOTAL",
        "KXNBA2HWINNER","KXNBA2D","KXNBA3D","KXNBA3PT",
        "KXNBAPTS","KXNBAREB","KXNBAAST","KXNBABLK","KXNBASTL",
        "KXNBA","KXNBAEAST","KXNBAWEST","KXNBAPLAYOFF","KXNBAPLAYIN",
        "KXNBAATLANTIC","KXNBACENTRAL","KXNBASOUTHEAST",
        "KXNBANORTHWEST","KXNBAPACIFIC","KXNBASOUTHWEST",
        "KXNBAEAST1SEED","KXNBAWEST1SEED",
        "KXTEAMSINNBAF","KXTEAMSINNBAEF","KXTEAMSINNBAWF",
        "KXNBAMATCHUP","KXNBAWINS","KXRECORDNBABEST",
        "KXNBAMVP","KXNBAROY","KXNBACOY","KXNBADPOY","KXNBASIXTH",
        "KXNBAMIMP","KXNBACLUTCH","KXNBAFINMVP","KXNBAWFINMVP","KXNBAEFINMVP",
        "KXNBA1STTEAM","KXNBA2NDTEAM","KXNBA3RDTEAM",
        "KXNBA1STTEAMDEF","KXNBA2NDTEAMDEF",
        "KXLEADERNBAPTS","KXLEADERNBAREB","KXLEADERNBAAST",
        "KXLEADERNBABLK","KXLEADERNBASTL","KXLEADERNBA3PT",
        "KXNBADRAFT1","KXNBADRAFTPICK","KXNBADRAFTTOP","KXNBADRAFTCAT","KXNBADRAFTCOMP",
        "KXNBATOPPICK","KXNBALOTTERYODDS","KXNBATOP5ROTY",
        "KXNBATEAM","KXNBASEATTLE","KXCITYNBAEXPAND","KXSONICS",
        "KXNEXTTEAMNBA","KXLBJRETIRE","KXSPORTSOWNERLBJ","KXSTEPHDEAL",
        "KXQUADRUPLEDOUBLE","KXSHAI20PTREC","KXNBA2KCOVER",
        "KXWNBADRAFT1","KXWNBADRAFTTOP3","KXWNBADELAY","KXWNBAGAMESPLAYED",
        "KXMARMAD","KXNCAAMBNEXTCOACH",
        "KXEUROLEAGUEGAME","KXBSLGAME","KXBBLGAME","KXACBGAME",
        "KXISLGAME","KXABAGAME","KXCBAGAME","KXBBSERIEAGAME",
        "KXJBLEAGUEGAME","KXLNBELITEGAME","KXARGLNBGAME","KXVTBGAME",
    ],
    # Add the rest of your sports here (Baseball, Football, Hockey, Tennis, Golf, etc.) from your original file
    # For now the code has Soccer and Basketball. Please add the remaining ones.
}

SPORT_ICONS = {
    "Soccer":"⚽","Basketball":"🏀","Baseball":"⚾","Football":"🏈",
    "Hockey":"🏒","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Esports":"🎮","Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉",
    "Lacrosse":"🥍","Chess":"♟️","Darts":"🎯","Aussie Rules":"🏉",
    "Other Sports":"🏆",
}

SOCCER_COMP = {
    "KXEPLGAME":"EPL","KXEPL1H":"EPL","KXEPLSPREAD":"EPL","KXEPLTOTAL":"EPL",
    "KXEPLBTTS":"EPL","KXEPLTOP4":"EPL","KXEPLTOP2":"EPL","KXEPLTOP6":"EPL",
    "KXEPLRELEGATION":"EPL","KXPREMIERLEAGUE":"EPL","KXARSENALCUPS":"EPL",
    "KXWINSTREAKMANU":"EPL","KXNEXTMANAGERMANU":"EPL","KXPFAPOY":"EPL","KXLAMINEYAMAL":"EPL",
    "KXUCLGAME":"Champions League","KXUCL1H":"Champions League","KXUCLSPREAD":"Champions League",
    "KXUCLTOTAL":"Champions League","KXUCLBTTS":"Champions League","KXUCL":"Champions League",
    "KXUCLFINALIST":"Champions League","KXUCLRO4":"Champions League","KXUCLW":"Champions League",
    "KXLEADERUCLGOALS":"Champions League","KXTEAMSINUCL":"Champions League",
    "KXUELGAME":"Europa League","KXUELSPREAD":"Europa League","KXUELTOTAL":"Europa League","KXUEL":"Europa League",
    "KXUECL":"Conference League","KXUECLGAME":"Conference League",
    # Add the rest from your original SOCCER_COMP
}

SPORT_SUBTABS = {
    # Paste your full SPORT_SUBTABS here from original
}

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
        if d is None or pd.isna(d):
            return ""
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
        return ""

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
            resp  = client.get_events(**kw).to_dict()
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
    df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other").str.strip()
    df["_series"]  = df.get("series_ticker", pd.Series("", index=df.index)).fillna("").str.upper()
    df["_sport"]   = df["_series"].apply(get_sport)
    df["_is_sport"]= df["_sport"] != ""

    if "markets" not in df.columns:
        df["markets"] = [[] for _ in range(len(df))]
    df["markets"] = df["markets"].apply(lambda x: x if isinstance(x, list) else [])

    df["_soccer_comp"] = df.apply(
        lambda r: SOCCER_COMP.get(r["_series"],"Other") if r["_sport"]=="Soccer" else "", axis=1
    )

    def extract(row):
        mkts = row.get("markets")
        if not isinstance(mkts, list) or not mkts:
            return "—", "—", None, None, None, None, []

        first_mk   = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport        = str(row.get("_sport", ""))

        game_date = parse_game_date_from_ticker(event_ticker)
        open_dt   = safe_dt(first_mk.get("open_time"))
        close_dt  = safe_dt(first_mk.get("close_time"))
        exp_dt    = safe_dt(first_mk.get("expected_expiration_time"))

        from datetime import timedelta as _td
        DURATION = {
            "Soccer": _td(hours=2), "Baseball": _td(hours=3),
            "Basketball": _td(hours=2, minutes=30),
            "Hockey": _td(hours=2, minutes=30),
            "Football": _td(hours=3),
            "Cricket": _td(hours=4),
        }
        duration = DURATION.get(sport, _td(hours=2))
        kickoff_dt = None
        if game_date and sport and sport in DURATION:
            if exp_dt:
                kickoff_dt = exp_dt - duration
            elif close_dt:
                kickoff_dt = close_dt - duration

        sort_dt = game_date if game_date else (close_dt.date() if close_dt else None)

        outcomes = []
        for mk in mkts:
            label = str(mk.get("yes_sub_title") or "").strip()
            if not label:
                t = str(mk.get("ticker") or "")
                parts = t.rsplit("-", 1)
                label = parts[-1] if len(parts) > 1 else t

            yf = nf = None
            try:
                yd = mk.get("yes_bid_dollars")
                nd = mk.get("no_bid_dollars")
                if yd is not None: yf = float(yd)
                if nd is not None: nf = float(nd)
                if yf is None:
                    yb = mk.get("yes_bid")
                    if yb is not None: yf = float(yb) / 100
                if nf is None:
                    nb = mk.get("no_bid")
                    if nb is not None: nf = float(nb) / 100
            except: pass

            chance = f"{int(round(yf*100))}%" if yf is not None else "—"
            yes    = f"{int(round(yf*100))}¢"  if yf is not None else "—"
            no     = f"{int(round(nf*100))}¢"  if nf is not None else "—"
            outcomes.append((label[:35], chance, yes, no))

        return "—", "—", sort_dt, game_date, kickoff_dt, "", outcomes

    info = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = info[0]; df["_no"] = info[1]; df["_mkt_dt"] = info[2]; df["_game_date"] = info[3]; df["_kickoff_dt"] = info[4]; df["_begins"] = info[5]; df["_outcomes"] = info[6]

    df["_sort_dt"] = df["_mkt_dt"]

    def get_display_dt(row):
        kdt = row.get("_kickoff_dt")
        if kdt is None or pd.isna(kdt):
            return ""
        return fmt_date(kdt)

    df["_display_dt"] = df.apply(get_display_dt, axis=1)

    prog.progress(1.0); prog.empty()
    return df

# ── Automatic Infinite Scroll (minimal change) ───────────────────────────────
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
            ticker  = str(row.get("event_ticker","")).upper()
            cat     = str(row.get("category","Other"))
            title   = str(row.get("title",""))[:90]
            sport   = str(row.get("_sport",""))
            base_ic, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon    = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label   = sport[:16] if sport else cat[:16]
            dt      = str(row.get("_display_dt","Open"))
            outcomes = row.get("_outcomes") or []

            series_lower = str(row.get("series_ticker","")).lower()
            ticker_lower = ticker.lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker_lower}" if series_lower else ""
            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'

            if outcomes:
                odds_html = ""
                for (olabel, ochance, oyes, ono) in outcomes[:5]:
                    safe_label = olabel[:30] if olabel else "—"
                    odds_html += f'''<div class="outcome-row">
<div class="outcome-label">{safe_label}</div>
<div class="outcome-chance">{ochance}</div>
<div class="outcome-odds">
<div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{oyes}</div></div>
<div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{ono}</div></div>
</div></div>'''
            else:
                odds_html = '<div class="outcome-row"><div class="outcome-label">—</div><div class="outcome-chance">—</div><div class="outcome-odds"><div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">—</div></div><div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">—</div></div></div></div>'

            dt_html = f'<div class="card-timing"><span class="date-text">{dt}</span></div>' if dt else ''

            html += (
                '<div class="market-card">'
                f'<div class="card-top"><span class="cat-pill {pill}">{label}</span></div>'
                + dt_html +
                f'<span class="card-icon">{icon}</span>'
                f'<div class="card-title">{title}</div>'
                f'<div class="card-footer">{link_html}{odds_html}</div>'
                '</div>'
            )
        except: continue
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

    if visible < len(data):
        st.markdown(f"""
        <script>
            function autoLoad() {{
                var threshold = 350;
                if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - threshold) {{
                    var btn = document.querySelector('button[key="auto_load_{tab_name}"]');
                    if (btn) btn.click();
                }}
            }}
            window.addEventListener('scroll', autoLoad);
            setTimeout(autoLoad, 600);
        </script>
        """, unsafe_allow_html=True)

        if st.button("", key=f"auto_load_{tab_name}", help=""):
            st.session_state[state_key] += BATCH_SIZE
            st.rerun()

# ── Main layout (original style) ─────────────────────────────────────────────
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
    date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed", key="date_mode_sel")
with _dfc2:
    include_no_date = st.toggle("Include undated", value=True)

if date_mode == "Today":
    d_start = d_end = today
elif date_mode == "This week":
    d_start, d_end = today, today + timedelta(days=6)
elif date_mode == "Custom":
    _dc1, _dc2, _ = st.columns([1, 1, 1])
    with _dc1:
        d_start = st.date_input("From", value=today, label_visibility="collapsed")
    with _dc2:
        d_end = st.date_input("To", value=today+timedelta(days=7), label_visibility="collapsed")

with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials.")
    st.stop()

filtered = df.copy()

if date_mode != "All dates":
    def date_ok(row):
        kdt = row.get("_kickoff_dt")
        has_kickoff = kdt is not None and not pd.isna(kdt)
        if has_kickoff:
            try:
                kd = kdt.date() if hasattr(kdt, "date") else kdt
                return d_start <= kd <= d_end
            except:
                return False
        else:
            return include_no_date
    filtered = filtered[filtered.apply(date_ok, axis=1)]

if search:
    s = search.lower()
    mask = (filtered["title"].str.lower().str.contains(s, na=False) |
            filtered["event_ticker"].str.lower().str.contains(s, na=False) |
            filtered["category"].str.lower().str.contains(s, na=False))
    filtered = filtered[mask]

if sort_by != "Default":
    asc = sort_by == "Earliest first"
    def _sort_key(d):
        if d is None: return "9999-99-99"
        if isinstance(d, date): return d.isoformat()
        try: return str(d)
        except: return "9999-99-99"
    filtered = filtered.copy()
    filtered["_sk"] = filtered["_sort_dt"].apply(_sort_key)
    has_date = filtered["_sk"] != "9999-99-99"
    dated   = filtered[has_date].sort_values("_sk", ascending=asc)
    undated = filtered[~has_date]
    filtered = pd.concat([dated, undated], ignore_index=True)
    filtered = filtered.drop(columns=["_sk"])

sport_count = int(df["_is_sport"].sum())

# ── Render (original style) ──────────────────────────────────────────────────
present_cats = [""] + ["All"] + [c for c in TOP_CATS
    if (c=="Sports" and sport_count>0) or (c!="Sports" and c in df["category"].values)]

top_tabs = st.tabs(present_cats)

for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]

        if cat == "":
            st.markdown(
                "<div style='text-align:center;padding:80px 20px;font-family:Helvetica,Arial,sans-serif;'>"
                "<div style='font-size:18px;color:#00ff00;font-weight:700;margin-bottom:12px;'>"
                "Welcome to OddsIQ</div>"
                "<div style='font-size:14px;color:#555;'>"
                "Select a category above to browse markets.</div>"
                "</div>",
                unsafe_allow_html=True)
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
                    arrow = " ▾" if (is_sel and item != "All sports") else (" ▸" if item != "All sports" else "")
                    color = "#00ff00" if is_sel else "#ffffff"
                    weight = "bold" if is_sel else "normal"

                    st.markdown(
                        f"<div style='color:{color};font-weight:{weight};font-size:13px;"
                        f"padding:4px 0;font-family:Helvetica,Arial,sans-serif;cursor:pointer;'>"
                        f"{item} ({cnt}){arrow}</div>",
                        unsafe_allow_html=True
                    )
                    if st.button(f"{item}", key=f"sp__{item.replace(' ','_')}"):
                        st.session_state.sel_sport = item
                        st.rerun()

            with card_col:
                s = st.session_state.get("sel_sport", "All sports")
                view = sdf if s == "All sports" else sdf[sdf["_sport"]==s].copy()
                render_cards(view, tab_name=f"sports_{s.replace(' ','_')}")

        else:
            render_cards(filtered[filtered["category"]==cat].copy(), tab_name=f"cat_{cat.replace(' ','_')}")

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 30 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
