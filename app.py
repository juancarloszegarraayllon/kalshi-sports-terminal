import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ==================== CSS ====================
st.markdown("""<style>
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:80px!important;line-height:1.1!important;}
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
.empty-state{text-align:center;padding:80px 20px;color:#666;font-size:14px;}
</style>""", unsafe_allow_html=True)

UTC = timezone.utc

# ==================== ALL METADATA (from your original file) ====================
TOP_CATS = ["Sports","Elections","Politics","Economics","Financials","Crypto","Companies",
            "Entertainment","Climate and Weather","Science and Technology","Health"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),"Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),"Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),"Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),"Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),"Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),
}

# SPORT SERIES → SPORT NAME
_SPORT_SERIES = {
    "Soccer": ["KXEPLGAME","KXEPL1H","KXEPLSPREAD","KXEPLTOTAL","KXEPLBTTS","KXUCLGAME","KXUCL","KXLALIGAGAME","KXSERIEAGAME","KXBUNDESLIGAGAME","KXMLSGAME","KXWCGAME"],  # shortened for example - keep your full list
    "Basketball": ["KXNBAGAME","KXNBA","KXNBAEAST","KXNBAWEST"],
    "Baseball": ["KXMLBGAME","KXMLB"],
    "Football": ["KXUFLGAME","KXSB","KXNFLPLAYOFF"],
    "Hockey": ["KXNHLGAME","KXNHL"],
    # ... Add the rest of your original _SPORT_SERIES dict here if you want full coverage
}

SPORT_ICONS = {
    "Soccer":"⚽","Basketball":"🏀","Baseball":"⚾","Football":"🏈",
    "Hockey":"🏒","Tennis":"🎾","Golf":"⛳","MMA":"🥊","Cricket":"🏏",
    "Esports":"🎮","Motorsport":"🏎️","Boxing":"🥊",
}

# Build SERIES_SPORT lookup
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

SOCCER_COMP = {}  # You can leave empty or add your full dict later

SPORT_SUBTABS = {}  # You can expand later

# ==================== HELPERS ====================
def parse_game_date_from_ticker(event_ticker):
    import re
    from datetime import date
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = str(event_ticker).split("-")
        if len(parts) < 2: return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if m:
            yy, mon, dd = m.group(1), m.group(2), m.group(3)
            return date(2000 + int(yy), MONTHS.get(mon, 1), int(dd))
    except:
        pass
    return None

def fmt_date(d):
    try:
        return d.strftime("%b %d") if hasattr(d, 'strftime') else str(d)
    except:
        return ""

# ==================== API ====================
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

@st.cache_data(ttl=900)
def fetch_all():
    with st.spinner("Loading markets from Kalshi..."):
        events = []
        cursor = None
        for i in range(25):
            try:
                kw = {"limit": 200, "status": "open", "with_nested_markets": True}
                if cursor:
                    kw["cursor"] = cursor
                resp = client.get_events(**kw).to_dict()
                batch = resp.get("events", [])
                events.extend(batch)
                cursor = resp.get("cursor") or resp.get("next_cursor")
                if not cursor or not batch:
                    break
                time.sleep(0.07)
            except Exception as e:
                st.error(f"API Error: {e}")
                break

        if not events:
            st.error("No events returned. Please try again later.")
            st.stop()

        df = pd.DataFrame(events)
        
        # Critical fixes
        df["category"] = df.get("category", pd.Series("Other", index=df.index)).fillna("Other")
        df["_series"] = df.get("series_ticker", pd.Series("", index=df.index)).fillna("").str.upper()
        df["_sport"] = df["_series"].map(SERIES_SPORT).fillna("")
        df["_is_sport"] = df["_sport"] != ""
        df["_game_date"] = df["event_ticker"].apply(parse_game_date_from_ticker)
        df["_display_dt"] = df["_game_date"].apply(fmt_date)

        # Outcome extraction
        def get_outcomes(mkts):
            if not isinstance(mkts, list):
                return []
            outs = []
            for m in mkts[:5]:
                label = str(m.get("yes_sub_title") or m.get("ticker","").split("-")[-1])[:30]
                try:
                    y = float(m.get("yes_bid_dollars") or (m.get("yes_bid") or 0)/100)
                    n = float(m.get("no_bid_dollars") or (m.get("no_bid") or 0)/100)
                    outs.append((label, f"{int(y*100)}%", f"{int(y*100)}¢", f"{int(n*100)}¢"))
                except:
                    outs.append((label, "—", "—", "—"))
            return outs

        df["_outcomes"] = df["markets"].apply(get_outcomes)

        st.success(f"✅ Loaded {len(df)} markets")
        return df

# ==================== RENDER CARDS ====================
def render_cards(data, page_size=30):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return

    if "card_page" not in st.session_state:
        st.session_state.card_page = 1

    total = len(data)
    total_pages = (total // page_size) + bool(total % page_size)
    page = max(1, min(st.session_state.card_page, total_pages))

    start = (page - 1) * page_size
    page_data = data.iloc[start : start + page_size]

    html = '<div class="card-grid">'
    for _, row in page_data.iterrows():
        try:
            ticker = str(row.get("event_ticker", "")).upper()
            title = str(row.get("title", ""))[:85]
            cat = str(row.get("category", "Other"))
            sport = str(row.get("_sport", ""))
            icon, pill = CAT_META.get(cat, ("📊", "pill-default"))
            icon = SPORT_ICONS.get(sport, icon) if sport else icon
            label = sport[:16] if sport else cat[:16]
            dt = row.get("_display_dt") or "Open"

            series_lower = str(row.get("series_ticker", "")).lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{ticker.lower()}" if series_lower else ""

            outcomes_html = ""
            for lab, ch, yes, no in row.get("_outcomes", []):
                outcomes_html += f'''
                <div class="outcome-row">
                    <div class="outcome-label">{lab}</div>
                    <div class="outcome-chance">{ch}</div>
                    <div class="outcome-odds">
                        <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{yes}</div></div>
                        <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{no}</div></div>
                    </div>
                </div>'''

            link = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else ticker

            html += f'''
            <div class="market-card">
                <div class="card-top"><span class="cat-pill {pill}">{label}</span></div>
                <div class="card-timing"><span class="date-text">{dt}</span></div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">{link}{outcomes_html}</div>
            </div>'''
        except:
            continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Pagination
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("← Previous", disabled=page <= 1, key="prev"):
            st.session_state.card_page -= 1
            st.rerun()
    with c2:
        st.markdown(f"<div style='text-align:center;color:#00ff00;'>Page {page} of {total_pages} ({total} total)</div>", unsafe_allow_html=True)
    with c3:
        if st.button("Next →", disabled=page >= total_pages, key="next"):
            st.session_state.card_page += 1
            st.rerun()

# ==================== MAIN UI ====================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-weight:800;margin:1rem 0;'>OddsIQ</div>", unsafe_allow_html=True)

if st.button("🔄 Refresh Data"):
    fetch_all.clear()
    if "card_page" in st.session_state:
        st.session_state.card_page = 1
    st.rerun()

df = fetch_all()

search = st.text_input("🔍 Search team, player or market", "", label_visibility="collapsed")

filtered = df.copy()
if search:
    s = search.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(s, na=False) |
        filtered["event_ticker"].str.lower().str.contains(s, na=False)
    ]

# Tabs
tab_list = st.tabs(["All Markets", "Sports"])

for i, tab in enumerate(tab_list):
    with tab:
        if i == 0:
            render_cards(filtered)
        else:
            sports_df = filtered[filtered["_is_sport"] == True]
            render_cards(sports_df)

st.caption("KALSHI TERMINAL • Updated every 15 minutes • Not financial advice")
