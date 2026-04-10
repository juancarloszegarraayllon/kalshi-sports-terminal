import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import tempfile

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== YOUR FULL CSS (Paste your original CSS here) ======================
st.markdown("""
<style>
/* ── Base ── */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}

/* Title */
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}

/* Metrics, Cards, Outcomes - Paste ALL your original CSS styles here */
.metric-strip{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;}
.metric-box{background:#0a0a0a;border:1px solid #00ff00;border-radius:8px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#00ff00;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;opacity:.7;}
.metric-value{font-size:24px;font-weight:700;color:#00ff00;}
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
/* Add the rest of your original CSS (nav, tabs, buttons, etc.) here if needed */
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# ====================== METADATA ======================
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials","Crypto","Companies",
            "Entertainment","Climate and Weather","Science and Technology","Health","Social",
            "World","Transportation","Mentions"]

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

SPORT_ICONS = {
    "Soccer":"⚽","Basketball":"🏀","Baseball":"⚾","Football":"🏈",
    "Hockey":"🏒","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Esports":"🎮","Motorsport":"🏎️","Boxing":"🥊","Rugby":"🏉",
    "Lacrosse":"🥍","Chess":"♟️","Darts":"🎯","Aussie Rules":"🏉","Other Sports":"🏆",
}

# ====================== PASTE YOUR BIG DICTIONARIES HERE ======================
# <<< PASTE _SPORT_SERIES FROM YOUR ORIGINAL FILE >>>
_SPORT_SERIES = {
    "Soccer": [  # ← Paste the full Soccer list here
        "KXEPLGAME","KXEPL1H","KXEPLSPREAD","KXEPLTOTAL","KXEPLBTTS", # ... all your soccer series
        # ... continue with all items from your original _SPORT_SERIES["Soccer"]
    ],
    "Basketball": [ # ← Paste full Basketball list
    ],
    "Baseball": [],
    "Football": [],
    "Hockey": [],
    "Tennis": [],
    "Golf": [],
    "MMA": [],
    "Cricket": [],
    "Esports": [],
    "Motorsport": [],
    "Boxing": [],
    "Rugby": [],
    "Lacrosse": [],
    "Chess": ["KXCHESSWORLDCHAMPION","KXCHESSCANDIDATES"],
    "Darts": ["KXDARTSMATCH","KXPREMDARTS"],
    "Aussie Rules": ["KXAFLGAME"],
    "Other Sports": ["KXSAILGP","KXPIZZASCORE9","KXROCKANDROLLHALLOFFAME",
                     "KXEUROVISIONISRAELBAN","KXCOLLEGEGAMEDAYGUEST","KXWSOPENTRANTS"],
}

# Build lookup (this fixes the previous errors)
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

# <<< PASTE SOCCER_COMP AND SPORT_SUBTABS FROM ORIGINAL FILE >>>
SOCCER_COMP = {}   # ← Paste your full SOCCER_COMP dictionary here
SPORT_SUBTABS = {} # ← Paste your full SPORT_SUBTABS dictionary here

# ====================== HELPERS ======================
def safe_dt(val):
    try:
        if not val: return None
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().astimezone(UTC) if not pd.isna(ts) else None
    except:
        return None

def parse_game_date_from_ticker(event_ticker):
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

# ====================== FETCH DATA ======================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_all():
    with st.spinner("🔄 Connecting to Kalshi... This may take 15-40 seconds on first load"):
        events = []
        cursor = None
        for i in range(20):
            try:
                resp = client.get_events(
                    limit=150,
                    status="open",
                    with_nested_markets=True,
                    cursor=cursor
                ).to_dict()

                batch = resp.get("events", [])
                if not batch:
                    break
                events.extend(batch)
                cursor = resp.get("cursor") or resp.get("next_cursor")
                if not cursor:
                    break
                time.sleep(0.05)
            except Exception as e:
                if "429" in str(e).lower():
                    time.sleep(3)
                else:
                    st.error(f"Kalshi API Error: {e}")
                    st.stop()
        return pd.DataFrame(events)

# ====================== PROCESS DATA ======================
@st.cache_data(ttl=600)
def process_markets(df):
    if df.empty:
        return df

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
            hours = {"Soccer":2, "Baseball":3, "Basketball":2.5, "Hockey":2.5, "Football":3}.get(sport, 2)
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

# ====================== MAIN APP ======================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([3, 1.4, 1])
with c1:
    search = st.text_input("", placeholder="🔍 Search team, player, market…", label_visibility="collapsed")
with c2:
    sort_by = st.selectbox("", ["Earliest first", "Latest first", "Default"], index=0, label_visibility="collapsed")
with c3:
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_all.clear()
        process_markets.clear()
        st.rerun()

date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")

with st.spinner("Loading and processing Kalshi markets..."):
    raw_df = fetch_all()

    if raw_df.empty:
        st.error("No data received. Check your Kalshi API keys in secrets.")
        st.stop()

    # Add sport column
    raw_df["category"] = raw_df.get("category", "Other").fillna("Other").str.strip()
    raw_df["_series"] = raw_df.get("series_ticker", "").fillna("").str.upper()
    raw_df["_sport"] = raw_df["_series"].map(lambda s: SERIES_SPORT.get(s, ""))
    raw_df["_is_sport"] = raw_df["_sport"] != ""

    df = process_markets(raw_df)

st.caption(f"Loaded {len(df)} open markets")

# ====================== FILTERING & RENDERING ======================
# Add your filtering logic, render_cards function, tabs, and Sports navigation here
# (You can copy them from your original file)

# For now, simple render to test if it works
if not df.empty:
    st.success("✅ App loaded successfully!")
    st.dataframe(df[["event_ticker", "title", "category", "_sport"]].head(20))
else:
    st.info("No markets to display yet.")

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · OPTIMIZED VERSION</p>", unsafe_allow_html=True)
