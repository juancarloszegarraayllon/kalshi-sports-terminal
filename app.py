import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import tempfile

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== FULL CSS (Paste your entire original <style> block here) ======================
st.markdown("""
<style>
/* ── Base ── */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}

/* Paste your ENTIRE original CSS here - from h1 styles down to the last :root{--primary} */
/* ... (keep everything exactly as in your original file) ... */
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ====================== CATEGORY METADATA ======================
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

CAT_TAGS = {
    "Elections":["US Elections","International","House","Senate","Primaries","Governor"],
    "Politics":["Trump","Congress","International","SCOTUS","Local","Tariffs"],
    "Economics":["Fed","Inflation","GDP","Jobs","Housing","Oil","Global"],
    "Financials":["S&P","Nasdaq","Metals","Agriculture","Oil & Gas","Treasuries"],
    "Crypto":["BTC","ETH","SOL","DOGE","XRP","BNB"],
    "Companies":["IPOs","Elon Musk","CEOs","Tech","Layoffs"],
    "Entertainment":["Music","Television","Movies","Awards","Video games"],
    "Climate and Weather":["Hurricanes","Temperature","Snow and rain","Climate change"],
    "Science and Technology":["AI","Space","Medicine","Energy"],
}

SPORT_ICONS = {
    "Soccer":"⚽","Basketball":"🏀","Baseball":"⚾","Football":"🏈",
    "Hockey":"🏒","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Esports":"🎮","Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉",
    "Lacrosse":"🥍","Chess":"♟️","Darts":"🎯","Aussie Rules":"🏉",
    "Other Sports":"🏆",
}

# ====================== CRITICAL: DEFINE _SPORT_SERIES FIRST ======================
_SPORT_SERIES = {
    "Soccer": [
        "KXEPLGAME","KXEPL1H","KXEPLSPREAD","KXEPLTOTAL","KXEPLBTTS",
        "KXEPLTOP4","KXEPLTOP2","KXEPLTOP6","KXEPLRELEGATION","KXPREMIERLEAGUE",
        # ... PUT THE ENTIRE ORIGINAL "Soccer" LIST HERE ...
        # (copy from your original file - it's very long)
    ],
    "Basketball": [ ... ],   # copy full list
    "Baseball": [ ... ],
    "Football": [ ... ],
    "Hockey": [ ... ],
    "Tennis": [ ... ],
    "Golf": [ ... ],
    "MMA": [ ... ],
    "Cricket": [ ... ],
    "Esports": [ ... ],
    "Motorsport": [ ... ],
    "Boxing": [ ... ],
    "Rugby": [ ... ],
    "Lacrosse": [ ... ],
    "Chess": ["KXCHESSWORLDCHAMPION","KXCHESSCANDIDATES"],
    "Darts":  ["KXDARTSMATCH","KXPREMDARTS"],
    "Aussie Rules": ["KXAFLGAME"],
    "Other Sports": [
        "KXSAILGP","KXPIZZASCORE9","KXROCKANDROLLHALLOFFAME",
        "KXEUROVISIONISRAELBAN","KXCOLLEGEGAMEDAYGUEST","KXWSOPENTRANTS",
    ],
}

# ====================== BUILD SERIES_SPORT LOOKUP ======================
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# ====================== OTHER DICTIONARIES ======================
SOCCER_COMP = { ... }        # ← Paste your full SOCCER_COMP here
SPORT_SUBTABS = { ... }      # ← Paste your full SPORT_SUBTABS here

# ====================== HELPERS ======================
def safe_dt(val):
    try:
        if not val: return None
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().astimezone(UTC) if not pd.isna(ts) else None
    except:
        return None

def parse_game_date_from_ticker(event_ticker: str):
    import re
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = str(event_ticker).split("-")
        if len(parts) < 2: return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m: return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        return date(2000 + int(yy), MONTHS.get(mon), int(dd))
    except:
        return None

def fmt_date(d):
    try:
        if not d: return ""
        if hasattr(d, 'hour'):
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} ET"
        return d.strftime("%b %d")
    except:
        return ""

# ====================== KALSHI CLIENT ======================
@st.cache_resource
def get_client():
    from kalshi_python_sync import Configuration, KalshiClient
    key_id = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str)
        pem = f.name
    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem
    return KalshiClient(cfg)

client = get_client()

# ====================== FETCH + PROCESS (Optimized) ======================
@st.cache_data(ttl=900, show_spinner="Fetching latest Kalshi markets...")
def fetch_all():
    events = []
    cursor = None
    for i in range(25):   # reduced from 30
        try:
            resp = client.get_events(limit=200, status="open", with_nested_markets=True, cursor=cursor).to_dict()
            batch = resp.get("events", [])
            if not batch: break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor: break
            time.sleep(0.04)
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                break
    if not events:
        return pd.DataFrame()

    df = pd.DataFrame(events)
    df["category"] = df.get("category", "Other").fillna("Other").str.strip()
    df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"] = df["_series"].map(get_sport)        # Fast lookup
    df["_is_sport"] = df["_sport"] != ""
    df["markets"] = df.get("markets", [[]]*len(df)).apply(lambda x: x if isinstance(x, list) else [])

    return df

@st.cache_data(ttl=900)
def process_markets(df):
    if df.empty: return df.copy()

    def extract_row(row):
        mkts = row.get("markets", [])
        if not mkts:
            return None, None, None, "", []
        first = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport = row.get("_sport", "")

        game_date = parse_game_date_from_ticker(event_ticker)
        exp_dt = safe_dt(first.get("expected_expiration_time"))

        kickoff_dt = None
        if game_date and sport:
            hours = {"Soccer":2,"Baseball":3,"Basketball":2.5,"Hockey":2.5,"Football":3}.get(sport, 2)
            if exp_dt:
                from datetime import timedelta
                kickoff_dt = exp_dt - timedelta(hours=hours)

        display_dt = fmt_date(kickoff_dt) if kickoff_dt else ""
        sort_dt = game_date

        outcomes = []
        for mk in mkts[:5]:
            label = str(mk.get("yes_sub_title") or "").strip() or str(mk.get("ticker","")).split("-")[-1]
            try:
                yf = float(mk.get("yes_bid_dollars") or (mk.get("yes_bid") or 0)/100)
                nf = float(mk.get("no_bid_dollars") or (mk.get("no_bid") or 0)/100)
                outcomes.append((label[:35], f"{int(round(yf*100))}%", f"{int(round(yf*100))}¢", f"{int(round(nf*100))}¢"))
            except:
                outcomes.append((label[:35], "—", "—", "—"))
        return sort_dt, game_date, kickoff_dt, display_dt, outcomes

    processed = df.apply(extract_row, axis=1, result_type="expand")
    df = df.copy()
    df[["_sort_dt", "_game_date", "_kickoff_dt", "_display_dt", "_outcomes"]] = processed
    return df

# ====================== REST OF YOUR APP ======================
# From here, continue with your original code:
# st.markdown title, controls, date filters, filtering logic, render_cards(), tabs, etc.

st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

# ... paste the rest of your original app code (controls, date filter, filtering, render_cards, navigation, etc.)

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 15 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
