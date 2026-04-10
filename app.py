import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

# ==================== CLEAN CSS (moved outside any function) ====================
CSS = """
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
.ticker-text{font-size:10px;color:#00ff00;opacity:.6;display:block;margin-bottom:8px;word-break:break-all;}

/* ── Outcomes ── */
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

/* Button overrides */
button[kind="primary"]{background:#00ff00!important;color:#000000!important;border:1px solid #00ff00!important;font-family:Helvetica,sans-serif!important;font-weight:700!important;}
button[kind="secondary"]{background:#0a0a0a!important;color:#00ff00!important;border:1px solid #333333!important;}
button[kind="secondary"]:hover{border-color:#00ff00!important;}
.stButton button {background:transparent !important; border:none !important;}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ── Rest of your app (imports, constants, functions) ─────────────────────────
UTC = timezone.utc

TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"), "Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"), "Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"), "Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"), "Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"), "Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"), "Social":("👥","pill-default"),
    "World":("🌐","pill-default"), "Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

# === PASTE ALL YOUR LARGE DICTIONARIES HERE ===
# _SPORT_SERIES, SPORT_ICONS, SERIES_SPORT, SOCCER_COMP, SPORT_SUBTABS, CAT_TAGS
# (copy them exactly from your original file)

_SPORT_SERIES = { ... }   # ← Paste your full _SPORT_SERIES here
SPORT_ICONS = { ... }
# ... continue pasting all the rest (SERIES_SPORT, SOCCER_COMP, SPORT_SUBTABS, etc.)

# Build SERIES_SPORT
SERIES_SPORT = {}
for sport, series_list in _SPORT_SERIES.items():
    for s in series_list:
        SERIES_SPORT[s] = sport

def get_sport(series_ticker):
    return SERIES_SPORT.get(str(series_ticker).upper(), "")

# Keep all your helper functions: safe_dt, parse_game_date_from_ticker, fmt_date, etc.
# (copy them from your original file)

# ── API Client & fetch_all (unchanged except cache) ─────────────────────────
@st.cache_resource
def get_client():
    from kalshi_python_sync import Configuration, KalshiClient
    key_id  = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str)
        pem = f.name
    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem
    return KalshiClient(cfg)

client = get_client()

def paginate(...):   # keep your paginate function
    ...

@st.cache_data(ttl=1800)
def fetch_all():
    # Your original fetch_all logic (unchanged)
    ...

# ── Lazy Loading render_cards ───────────────────────────────────────────────
def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return

    BATCH_SIZE = 24
    STATE_KEY = "visible_count"

    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = BATCH_SIZE

    visible = min(len(data), st.session_state[STATE_KEY])
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

    if visible < len(data):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("↓ Load More Markets", type="primary", use_container_width=True):
                st.session_state[STATE_KEY] += BATCH_SIZE
                st.rerun()
        st.markdown(f"<p style='text-align:center;color:#888888;font-size:13px;'>Showing {visible} of {len(data)} markets</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align:center;color:#00ff00;font-size:13px;margin-top:24px;'>🎉 You've reached the end</p>", unsafe_allow_html=True)

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

# Search, Sort, Refresh row
_c1, _c2, _c3 = st.columns([3, 1.4, 1])
with _c1:
    search = st.text_input("", placeholder="🔍 Search team, player, market…", label_visibility="collapsed")
with _c2:
    sort_by = st.selectbox("", ["Earliest first","Latest first","Default"], index=0, label_visibility="collapsed")
with _c3:
    if st.button("Refresh", use_container_width=True):
        fetch_all.clear()
        st.session_state.pop("visible_count", None)
        st.rerun()

# Date filter
today = date.today()
_dfc1, _dfc2 = st.columns([2, 1])
with _dfc1:
    date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")
with _dfc2:
    include_no_date = st.toggle("Include undated", value=True)

if date_mode == "Today":
    d_start = d_end = today
elif date_mode == "This week":
    d_start, d_end = today, today + timedelta(days=6)
elif date_mode == "Custom":
    _dc1, _dc2, _ = st.columns([1, 1, 1])
    with _dc1: d_start = st.date_input("From", value=today)
    with _dc2: d_end = st.date_input("To", value=today+timedelta(days=7))
else:
    d_start = d_end = None

with st.spinner("Loading markets..."):
    df = fetch_all()

if df.empty:
    st.error("No data. Check API credentials.")
    st.stop()

# Apply filters
filtered = df.copy()

# Reset lazy loading when filters change
filter_hash = hash((search, date_mode, str(d_start), str(d_end), include_no_date, sort_by))
if "last_filter_hash" not in st.session_state or st.session_state.last_filter_hash != filter_hash:
    st.session_state.visible_count = 24
    st.session_state.last_filter_hash = filter_hash

# ... (keep your date filtering, search filtering, sorting logic exactly as before)

# ── Tabs & Rendering ─────────────────────────────────────────────────────────
present_cats = [""] + ["All"] + [c for c in TOP_CATS if (c=="Sports" and int(df["_is_sport"].sum()) > 0) or (c != "Sports" and c in df["category"].values)]

top_tabs = st.tabs(present_cats)

for i, tab in enumerate(top_tabs):
    with tab:
        cat = present_cats[i]
        if cat == "":
            # welcome message
            pass
        elif cat == "All":
            render_cards(filtered)
        elif cat == "Sports":
            # your sports navigation logic
            sdf = filtered[filtered["_is_sport"]].copy()
            # ... your nav_col + card_col logic ...
            render_cards(view)   # use the lazy version
        else:
            render_cards(filtered[filtered["category"] == cat].copy())

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 30 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
