import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ── CSS (unchanged) ─────────────────────────────────────────────────────────
st.markdown("""<style>
/* (Your full CSS block from the original app.py - kept exactly the same) */
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}
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
.begins-text{font-size:11px;color:#00ff00;font-weight:600;}
.live-text{font-size:11px;color:#00ff00;font-weight:700;}
.card-icon{font-size:20px;margin-bottom:4px;display:block;}
.card-title{font-size:14px;font-weight:600;color:#ffffff;line-height:1.45;margin-bottom:12px;min-height:52px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1c1c1c;padding-top:10px;}
.ticker-link{font-size:10px;color:#00ff00;letter-spacing:.04em;display:block;margin-bottom:8px;word-break:break-all;text-decoration:none;opacity:.6;}
.ticker-link:hover{opacity:1;text-decoration:underline;}
.ticker-text{font-size:10px;color:#00ff00;opacity:.6;display:block;margin-bottom:8px;word-break:break-all;}
.outcome-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;}
.outcome-label{font-size:11px;color:#ffffff;font-weight:500;flex:0 0 auto;min-width:80px;max-width:130px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.85;}
.outcome-chance{font-size:13px;font-weight:700;color:#ffffff;flex:0 0 auto;min-width:38px;text-align:right;}
.outcome-odds{display:flex;gap:6px;flex:1;justify-content:flex-end;}
.outcome-odds .odds-yes,.outcome-odds .odds-no{flex:0 0 auto;min-width:52px;}
.odds-yes{background:#001500;border:1px solid #00ff00;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{background:#150000;border:1px solid #ff2222;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#ffffff;text-transform:uppercase;letter-spacing:.08em;opacity:.5;}
.odds-price-yes{font-size:15px;font-weight:700;color:#00ff00;}
.odds-price-no{font-size:15px;font-weight:700;color:#ff2222;}
.empty-state{text-align:center;padding:80px 20px;color:#333;font-size:14px;}
hr{border-color:#1c1c1c!important;}
/* Nav & button overrides (kept the same) */
button[kind="secondary"], button[kind="primary"], div[data-testid="stButton"] button, .stButton > div > button, .stButton button {
    background: transparent !important; border: none !important; box-shadow: none !important; color: #ffffff !important;
    font-family: Helvetica, Arial, sans-serif !important; font-size: 13px !important; padding: 3px 0 !important;
}
.stTabs [data-baseweb="tab-list"]{background:#000000;border-bottom:1px solid #00ff00;}
.stTabs [aria-selected="true"]{background:#001500!important;color:#00ff00!important;}
</style>""", unsafe_allow_html=True)

UTC = timezone.utc

# ── All your original metadata (CAT_META, SERIES_SPORT, SOCCER_COMP, SPORT_SUBTABS, etc.) ──
# (I kept them exactly as in your original file - copy-paste them here)

# ... [Paste all the TOP_CATS, CAT_META, SERIES_SPORT, _SPORT_SERIES, SPORT_ICONS, SOCCER_COMP, SPORT_SUBTABS, SERIES_TO_SUBTAB here - unchanged] ...

# Helpers (kept mostly the same, with small improvements)
def safe_dt(val):
    try:
        if val is None or val == "": return None
        ts = pd.to_datetime(val, utc=True)
        if pd.isna(ts): return None
        return ts.to_pydatetime().astimezone(UTC)
    except:
        return None

def parse_game_date_from_ticker(event_ticker: str):
    import re
    from datetime import date
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = event_ticker.split("-")
        if len(parts) < 2: return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m: return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        return date(2000 + int(yy), MONTHS[mon], int(dd))
    except:
        return None

def fmt_date(d):
    try:
        if d is None: return ""
        if hasattr(d, 'hour'):
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} ET"
        return d.strftime("%b %d")
    except:
        return str(d) if d else ""

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f<=1.0 else int(round(f))}%"
    except:
        return "—"

# ── API Client ─────────────────────────────────────────────────────────────
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

# Improved pagination
def paginate(with_markets=False, category=None, max_pages=20):
    events = []
    cursor = None
    for i in range(max_pages):
        try:
            kw = {"limit": 200, "status": "open"}
            if with_markets:
                kw["with_nested_markets"] = True
            if category:
                kw["category"] = category
            if cursor:
                kw["cursor"] = cursor

            resp = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            if not batch:
                break
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            if not cursor:
                break
            if i > 0:  # lighter sleep
                time.sleep(0.07)
        except Exception as e:
            if "429" in str(e):
                time.sleep(3)
            else:
                st.warning(f"API error: {e}")
                break
    return events

# ── Main Data Fetch (optimized) ─────────────────────────────────────────────
@st.cache_data(ttl=900)  # 15 minutes instead of 30
def fetch_all():
    with st.spinner("Loading markets from Kalshi..."):
        all_ev = paginate(with_markets=True, max_pages=20)
        if not all_ev:
            st.error("No events returned from Kalshi.")
            return pd.DataFrame()

        df = pd.DataFrame(all_ev)
        df["category"] = df.get("category", "Other").fillna("Other").str.strip()
        df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
        df["_sport"] = df["_series"].map(SERIES_SPORT).fillna("")
        df["_is_sport"] = df["_sport"] != ""

        # Vectorized date parsing
        df["_game_date"] = df["event_ticker"].apply(parse_game_date_from_ticker)

        def extract_outcomes(mkts):
            outcomes = []
            for mk in mkts[:5]:  # limit to first 5 outcomes
                label = str(mk.get("yes_sub_title") or mk.get("ticker", "").split("-")[-1]).strip()[:35]
                try:
                    yf = float(mk.get("yes_bid_dollars") or mk.get("yes_bid", 0)/100 or 0)
                    nf = float(mk.get("no_bid_dollars") or mk.get("no_bid", 0)/100 or 0)
                    chance = f"{int(round(yf*100))}%"
                    yes = f"{int(round(yf*100))}¢"
                    no = f"{int(round(nf*100))}¢"
                except:
                    chance = yes = no = "—"
                outcomes.append((label, chance, yes, no))
            return outcomes

        df["_outcomes"] = df["markets"].apply(lambda x: extract_outcomes(x) if isinstance(x, list) else [])

        # Simple kickoff / display date estimation
        def get_display_dt(row):
            gd = row.get("_game_date")
            if gd:
                return gd.strftime("%b %d")
            return "Open"
        df["_display_dt"] = df.apply(get_display_dt, axis=1)

        return df

# ── Render Cards with Pagination ────────────────────────────────────────────
def render_cards(data, page_size=40):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return

    total = len(data)
    page = st.session_state.get("card_page", 1)
    total_pages = (total // page_size) + (1 if total % page_size else 0)
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = start + page_size
    page_data = data.iloc[start:end]

    html = '<div class="card-grid">'
    for _, row in page_data.iterrows():
        try:
            ticker = str(row.get("event_ticker", "")).upper()
            cat = str(row.get("category", "Other"))
            title = str(row.get("title", ""))[:90]
            sport = str(row.get("_sport", ""))
            base_ic, pill = CAT_META.get(cat, ("📊", "pill-default"))
            icon = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label = sport[:16] if sport else cat[:16]
            dt = str(row.get("_display_dt", "Open"))

            series_lower = str(row.get("series_ticker", "")).lower()
            ticker_lower = ticker.lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker_lower}" if series_lower else ""

            outcomes = row.get("_outcomes", [])
            odds_html = ""
            for (olabel, ochance, oyes, ono) in outcomes:
                odds_html += f'''
                <div class="outcome-row">
                    <div class="outcome-label">{olabel}</div>
                    <div class="outcome-chance">{ochance}</div>
                    <div class="outcome-odds">
                        <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{oyes}</div></div>
                        <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{ono}</div></div>
                    </div>
                </div>'''

            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'

            html += f'''
            <div class="market-card">
                <div class="card-top"><span class="cat-pill {pill}">{label}</span></div>
                <div class="card-timing"><span class="date-text">{dt}</span></div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">{link_html}{odds_html}</div>
            </div>'''
        except:
            continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Previous", disabled=page <= 1):
            st.session_state.card_page = page - 1
            st.rerun()
    with col2:
        st.markdown(f"<div style='text-align:center; color:#00ff00; font-size:13px;'>Page {page} of {total_pages} ({total} total)</div>", unsafe_allow_html=True)
    with col3:
        if st.button("Next →", disabled=page >= total_pages):
            st.session_state.card_page = page + 1
            st.rerun()

# ── Rest of your app layout (tabs, filtering, Sports nav, etc.) ─────────────
# (Copy the rest of your original code from st.markdown title down to the end,
#  but replace the old render_cards(filtered) calls with the new render_cards function above.
#  Also reset st.session_state.card_page = 1 when filters change.)

# Quick example for the main "All" tab:
# with tab:
#     if cat == "All":
#         if "card_page" not in st.session_state:
#             st.session_state.card_page = 1
#         render_cards(filtered)

# Do the same for Sports sub-views and other categories.

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 15 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
