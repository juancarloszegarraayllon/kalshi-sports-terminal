import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ==================== FULL CSS (unchanged - your original) ====================
st.markdown("""<style>
html,body,[class*="css"]{font-family:Helvetica,Arial,sans-serif!important;background:#000000!important;color:#ffffff!important;}
section[data-testid="stSidebar"]{display:none!important;}
.stMainBlockContainer{padding-left:2rem!important;padding-right:2rem!important;}
.stApp{background:#000000!important;}
h1,h1 *,.css-10trblm,div[data-testid='stMarkdownContainer'] h1{font-family:Helvetica,Arial,sans-serif!important;font-weight:800!important;color:#00ff00!important;font-size:120px!important;line-height:1.1!important;}
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

# ==================== YOUR METADATA (copy from your original file) ====================
# Paste ALL of these exactly as they were in your original app.py:
# TOP_CATS, CAT_META, _SPORT_SERIES, SERIES_SPORT, SPORT_ICONS, SOCCER_COMP,
# SPORT_SUBTABS, SERIES_TO_SUBTAB, CAT_TAGS, etc.

# (For brevity I'm not repeating the 500+ line metadata here — copy it from your original file into this spot)

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
            return date(2000 + int(yy), MONTHS.get(mon), int(dd))
    except:
        pass
    return None

def fmt_date(d):
    try:
        return d.strftime("%b %d") if d else ""
    except:
        return str(d) if d else ""

# ==================== API CLIENT ====================
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

# ==================== FETCH DATA (improved + debug) ====================
@st.cache_data(ttl=900)
def fetch_all():
    progress = st.progress(0, text="Connecting to Kalshi...")
    events = []
    cursor = None
    try:
        for i in range(25):  # increased max pages slightly
            kw = {"limit": 200, "status": "open", "with_nested_markets": True}
            if cursor:
                kw["cursor"] = cursor
            resp = client.get_events(**kw).to_dict()
            batch = resp.get("events", [])
            events.extend(batch)
            cursor = resp.get("cursor") or resp.get("next_cursor")
            progress.progress(min(0.9, (i+1)/25), text=f"Loaded {len(events)} events...")
            if not cursor or not batch:
                break
            time.sleep(0.06)
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        st.stop()

    if not events:
        st.error("No open events returned from Kalshi. Try again later.")
        st.stop()

    df = pd.DataFrame(events)
    df["category"] = df.get("category", "Other").fillna("Other")
    df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"] = df["_series"].map(SERIES_SPORT).fillna("")
    df["_is_sport"] = df["_sport"] != ""
    df["_game_date"] = df["event_ticker"].apply(parse_game_date_from_ticker)
    df["_display_dt"] = df["_game_date"].apply(fmt_date)

    # Simple outcome extraction (first 5 only)
    def get_outcomes(markets):
        if not isinstance(markets, list) or not markets:
            return []
        outs = []
        for m in markets[:5]:
            label = str(m.get("yes_sub_title") or m.get("ticker","").split("-")[-1])[:35]
            try:
                y = float(m.get("yes_bid_dollars") or (m.get("yes_bid") or 0)/100)
                n = float(m.get("no_bid_dollars") or (m.get("no_bid") or 0)/100)
                outs.append((label, f"{int(y*100)}%", f"{int(y*100)}¢", f"{int(n*100)}¢"))
            except:
                outs.append((label, "—", "—", "—"))
        return outs

    df["_outcomes"] = df["markets"].apply(get_outcomes)

    progress.empty()
    st.success(f"✅ Loaded {len(df)} events successfully")
    return df

# ==================== RENDER CARDS WITH PAGINATION ====================
def render_cards(data, page_size=30):
    if data.empty:
        st.markdown('<div class="empty-state">No markets match your filters.</div>', unsafe_allow_html=True)
        return

    if "card_page" not in st.session_state:
        st.session_state.card_page = 1

    total = len(data)
    total_pages = (total // page_size) + (1 if total % page_size else 0)
    page = st.session_state.card_page
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    page_data = data.iloc[start:start + page_size]

    html = '<div class="card-grid">'
    for _, row in page_data.iterrows():
        try:
            ticker = str(row.get("event_ticker","")).upper()
            cat = str(row.get("category","Other"))
            title = str(row.get("title",""))[:85]
            sport = str(row.get("_sport",""))
            icon, pill = CAT_META.get(cat, ("📊","pill-default"))
            icon = SPORT_ICONS.get(sport, icon) if sport else icon
            label = (sport or cat)[:16]
            dt = row.get("_display_dt") or "Open"

            series_lower = str(row.get("series_ticker","")).lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker.lower()}" if series_lower else ""

            outcomes_html = ""
            for label_out, chance, yes, no in row.get("_outcomes", []):
                outcomes_html += f'''
                <div class="outcome-row">
                    <div class="outcome-label">{label_out}</div>
                    <div class="outcome-chance">{chance}</div>
                    <div class="outcome-odds">
                        <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{yes}</div></div>
                        <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{no}</div></div>
                    </div>
                </div>'''

            link = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'

            html += f'''
            <div class="market-card">
                <div class="card-top"><span class="cat-pill {pill}">{label}</span></div>
                <div class="card-timing"><span class="date-text">{dt}</span></div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">{link}{outcomes_html}</div>
            </div>'''
        except Exception:
            continue
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Pagination
    c1, c2, c3 = st.columns([1,2,1])
    with c1:
        if st.button("← Previous", disabled=page <= 1):
            st.session_state.card_page = page - 1
            st.rerun()
    with c2:
        st.markdown(f"<p style='text-align:center;color:#00ff00;'>Page {page} of {total_pages} — {total} markets</p>", unsafe_allow_html=True)
    with c3:
        if st.button("Next →", disabled=page >= total_pages):
            st.session_state.card_page = page + 1
            st.rerun()

# ==================== MAIN APP ====================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-weight:800;margin-bottom:1rem;'>OddsIQ</div>", unsafe_allow_html=True)

# Refresh button
if st.button("🔄 Refresh Data"):
    fetch_all.clear()
    st.rerun()

df = fetch_all()

if df.empty:
    st.stop()

# Simple search and date filter (you can expand later)
search = st.text_input("🔍 Search markets", placeholder="Team, player, election...", label_visibility="collapsed")

filtered = df.copy()
if search:
    s = search.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(s, na=False) |
        filtered["event_ticker"].str.lower().str.contains(s, na=False)
    ]

# ==================== TABS ====================
tabs = st.tabs(["All"] + [c for c in ["Sports", "Elections", "Politics"] if c in df["category"].unique() or c == "Sports"])

for tab in tabs:
    with tab:
        label = tab.label  # Streamlit tabs have .label in newer versions, adjust if needed
        if label == "All":
            render_cards(filtered)
        elif label == "Sports":
            sdf = filtered[filtered["_is_sport"]]
            render_cards(sdf)
        else:
            render_cards(filtered[filtered["category"] == label])

st.caption("KALSHI TERMINAL • Data cached 15 min • Not financial advice")
