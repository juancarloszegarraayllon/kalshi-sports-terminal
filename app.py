import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta

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
.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.cat-pill { font-size: 10px; font-weight: 500; letter-spacing: .1em; text-transform: uppercase; padding: 3px 10px; border-radius: 4px; border: 1px solid; }
.cat-Sports        { background: #1a2e1a; color: #4ade80; border-color: #166534; }
.cat-Politics      { background: #1e1a2e; color: #818cf8; border-color: #3730a3; }
.cat-Elections     { background: #2e1a1e; color: #f472b6; border-color: #9d174d; }
.cat-Financials    { background: #2e2a1a; color: #fbbf24; border-color: #92400e; }
.cat-Entertainment { background: #2e1e1a; color: #fb923c; border-color: #9a3412; }
.cat-Climate       { background: #1a2e2e; color: #22d3ee; border-color: #164e63; }
.cat-Science       { background: #1e2e1a; color: #86efac; border-color: #14532d; }
.cat-Health        { background: #2e1a2e; color: #e879f9; border-color: #701a75; }
.cat-default       { background: #1e1e32; color: #94a3b8; border-color: #2d2d55; }
.date-text { font-size: 11px; color: #374151; }
.card-title { font-size: 15px; font-weight: 500; color: #e2e8f0; line-height: 1.45; margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-icon { font-size: 22px; margin-bottom: 8px; display: block; }
.card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #1a1a2e; padding-top: 10px; }
.ticker-text { font-size: 10px; color: #374151; letter-spacing: .06em; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.empty-state { text-align: center; padding: 80px 20px; color: #374151; font-size: 14px; }
hr { border-color: #1e1e32 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0f0f1a; border-bottom: 1px solid #1e1e32; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #4b5563; border: none; font-size: 12px; letter-spacing: .06em; }
.stTabs [aria-selected="true"] { background: #1e1e32 !important; color: #a5b4fc !important; border-radius: 6px 6px 0 0; }
</style>
""", unsafe_allow_html=True)

# ── API ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    try:
        from kalshi_python_sync import Configuration, KalshiClient
        api_key_id = st.secrets["KALSHI_API_KEY_ID"]
        private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
            f.write(private_key_str)
            pem_path = f.name
        cfg = Configuration()
        cfg.api_key_id = api_key_id
        cfg.private_key_pem_path = pem_path
        return KalshiClient(cfg)
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.stop()

client = get_client()

# ── Fetch ALL events with rate-limit-safe pagination ──────────────────────────
@st.cache_data(ttl=600)  # cache for 10 min so we don't re-paginate constantly
def fetch_all():
    all_events = []
    cursor = None
    page = 0
    MAX_PAGES = 30
    DELAY = 0.4  # 400ms between requests — stays well under rate limit

    progress = st.progress(0, text="Fetching page 1…")

    while page < MAX_PAGES:
        try:
            kwargs = {"limit": 200, "status": "open"}
            if cursor:
                kwargs["cursor"] = cursor

            resp = client.get_events(**kwargs)
            data = resp.to_dict()
            events = data.get("events", [])

            if not events:
                break

            all_events.extend(events)
            page += 1

            # Update progress
            progress.progress(
                min(page / MAX_PAGES, 1.0),
                text=f"Fetched {len(all_events)} events across {page} pages…"
            )

            # Get next cursor
            cursor = (
                data.get("cursor") or
                data.get("next_cursor") or
                (data.get("pagination") or {}).get("next_cursor")
            )

            if not cursor:
                break  # last page

            time.sleep(DELAY)  # respect rate limit

        except Exception as e:
            err = str(e)
            if "429" in err or "too_many_requests" in err.lower():
                # Back off and retry once
                progress.progress(page / MAX_PAGES, text=f"Rate limited — waiting 3s then retrying…")
                time.sleep(3)
                continue
            else:
                st.warning(f"Stopped at page {page}: {e}")
                break

    progress.empty()

    if not all_events:
        return pd.DataFrame()

    df = pd.DataFrame(all_events)
    if "event_ticker" in df.columns:
        df = df.drop_duplicates(subset=["event_ticker"])

    # Parse dates
    for col in ["strike_date", "end_date", "close_time", "expiration_time"]:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
            if parsed.notna().any():
                df["_parsed_date"] = parsed
                break
    if "_parsed_date" not in df.columns:
        df["_parsed_date"] = pd.NaT

    # Normalize category
    if "category" not in df.columns:
        df["category"] = "Other"
    df["category"] = df["category"].fillna("Other").str.strip()

    return df

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Kalshi Terminal")
    search = st.text_input("Search", placeholder="soccer, tennis, team…")
    if st.button("🔄 Refresh data"):
        fetch_all.clear()
        st.rerun()
    st.caption("Data cached for 10 min to avoid rate limits.")

# ── Load ───────────────────────────────────────────────────────────────────────
st.title("📡 Kalshi Markets Terminal")

with st.spinner("Loading…"):
    df = fetch_all()

if df.empty:
    st.markdown('<div class="empty-state">No data returned. Check your API credentials.</div>', unsafe_allow_html=True)
    st.stop()

# ── Search ─────────────────────────────────────────────────────────────────────
filtered = df.copy()
if search:
    mask = (
        filtered.get("title", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
        filtered.get("event_ticker", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
        filtered.get("category", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

# ── Metrics ────────────────────────────────────────────────────────────────────
categories  = sorted(filtered["category"].unique().tolist())
tab_labels  = ["All"] + categories
sport_count = int((filtered["category"].str.lower() == "sports").sum())

st.markdown(f"""
<div class="metric-strip">
  <div class="metric-box"><div class="metric-label">Total markets</div><div class="metric-value">{len(df)}</div></div>
  <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sport_count}</div></div>
  <div class="metric-box"><div class="metric-label">Showing</div><div class="metric-value">{len(filtered)}</div></div>
  <div class="metric-box"><div class="metric-label">Categories</div><div class="metric-value">{len(categories)}</div></div>
</div>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_icon(ticker, category):
    t = ticker.upper()
    c = str(category).lower()
    if "NBA"    in t: return "🏀"
    if "MLB"    in t: return "⚾"
    if "NHL"    in t: return "🏒"
    if "NFL"    in t: return "🏈"
    if "GOLF"   in t or "PGA"  in t: return "⛳"
    if "TEN"    in t or "ATP"  in t or "WTA" in t: return "🎾"
    if "SOC"    in t or "MLS"  in t or "EPL" in t or "FIFA" in t or "UEFA" in t: return "⚽"
    if "UFC"    in t or "MMA"  in t: return "🥊"
    if "F1"     in t or "NASCAR" in t: return "🏎️"
    if "NCAAB"  in t: return "🏀"
    if "NCAAF"  in t: return "🏈"
    if "sport"  in c: return "🏟️"
    if "election" in c or "polit" in c: return "🗳️"
    if "financ" in c or "econom" in c: return "📈"
    if "entertain" in c: return "🎬"
    if "climate" in c or "weather" in c: return "🌍"
    if "science" in c or "tech" in c: return "🔬"
    if "health" in c: return "🏥"
    return "📊"

def get_pill_class(category):
    mapping = {
        "Sports":                 "cat-Sports",
        "Politics":               "cat-Politics",
        "Elections":              "cat-Elections",
        "Financials":             "cat-Financials",
        "Entertainment":          "cat-Entertainment",
        "Climate and Weather":    "cat-Climate",
        "Science and Technology": "cat-Science",
        "Health":                 "cat-Health",
    }
    return mapping.get(str(category), "cat-default")

def render_cards(data):
    if data.empty:
        st.markdown('<div class="empty-state">No markets here.</div>', unsafe_allow_html=True)
        return

    cards_html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker    = str(row.get("event_ticker", "")).upper()
            category  = str(row.get("category", "Other"))
            title_raw = str(row.get("title", "Unknown"))
            title     = title_raw.split(":")[-1].replace("Will the ", "").split("?")[0].strip() or title_raw[:80]
            icon      = get_icon(ticker, category)
            pill_cls  = get_pill_class(category)
            cat_label = category[:14]

            d = row.get("_parsed_date")
            try:
                display_date = pd.Timestamp(d).tz_convert("US/Eastern").strftime("%b %d") if pd.notna(d) else "Open"
            except Exception:
                display_date = "Open"

            cards_html += f"""
            <div class="market-card">
                <div class="card-top">
                    <span class="cat-pill {pill_cls}">{cat_label}</span>
                    <span class="date-text">{display_date}</span>
                </div>
                <span class="card-icon">{icon}</span>
                <div class="card-title">{title}</div>
                <div class="card-footer">
                    <span class="ticker-text">{ticker}</span>
                    <span class="status-dot"></span>
                </div>
            </div>"""
        except Exception:
            continue
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tabs = st.tabs(tab_labels)
for i, tab in enumerate(tabs):
    with tab:
        cat = tab_labels[i]
        if cat == "All":
            render_cards(filtered)
        else:
            render_cards(filtered[filtered["category"] == cat])

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1f2937;font-size:11px;letter-spacing:.06em;'>"
    "KALSHI TERMINAL · CACHED 10 MIN · NOT FINANCIAL ADVICE</p>",
    unsafe_allow_html=True
)
