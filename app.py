import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import tempfile

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== CSS (unchanged) ======================
st.markdown("""<style> ... (your entire <style> block here - no changes) </style>""", unsafe_allow_html=True)

UTC = timezone.utc

# ====================== Your existing constants (TOP_CATS, CAT_META, etc.) ======================
# ... paste all your TOP_CATS, CAT_META, CAT_TAGS, SERIES_SPORT, SOCCER_COMP, SPORT_SUBTABS, etc. unchanged ...

# ====================== Optimized Helpers ======================
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
        if not d: return ""
        if hasattr(d, 'hour'):
            # Simple ET conversion (you can keep pytz/zoneinfo if needed)
            hour = d.hour % 12 or 12
            ampm = "am" if d.hour < 12 else "pm"
            return f"{d.strftime('%b')} {d.day}, {hour}:{d.strftime('%M')}{ampm} ET"
        return d.strftime("%b %d")
    except:
        return ""

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f <= 1.0 else int(round(f))}%"
    except:
        return "—"

# ====================== API Client ======================
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

# ====================== Optimized Data Fetch ======================
@st.cache_data(ttl=900, show_spinner="Fetching latest markets from Kalshi...")  # 15 min cache
def fetch_all(max_pages=20):  # Reduced default from 30
    events = []
    cursor = None

    progress = st.progress(0, text="Connecting to Kalshi...")

    for i in range(max_pages):
        try:
            resp = client.get_events(
                limit=200,
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

            progress.progress(min(0.9, (i+1)/max_pages), text=f"Loaded {len(events)} events...")
            time.sleep(0.03)  # Very light throttle
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                st.warning(f"API error on page {i}: {e}")
                break

    progress.empty()
    if not events:
        st.error("No events returned from Kalshi.")
        return pd.DataFrame()

    df = pd.DataFrame(events)
    df["category"] = df.get("category", "Other").fillna("Other").str.strip()
    df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"] = df["_series"].apply(lambda s: SERIES_SPORT.get(s, ""))
    df["_is_sport"] = df["_sport"] != ""

    # Ensure markets is always list
    df["markets"] = df.get("markets", [[]] * len(df)).apply(lambda x: x if isinstance(x, list) else [])

    return df

# ====================== Process Markets (cached separately) ======================
@st.cache_data(ttl=900)
def process_markets(df: pd.DataFrame):
    if df.empty:
        return df

    def extract_row(row):
        mkts = row.get("markets", [])
        if not mkts:
            return None, None, None, None, None, [], ""

        first = mkts[0]
        event_ticker = str(row.get("event_ticker", ""))
        sport = str(row.get("_sport", ""))

        game_date = parse_game_date_from_ticker(event_ticker)
        exp_dt = safe_dt(first.get("expected_expiration_time"))
        close_dt = safe_dt(first.get("close_time"))

        # Simple kickoff estimate
        kickoff_dt = None
        if game_date and sport:
            duration_hours = {"Soccer": 2, "Baseball": 3, "Basketball": 2.5, "Hockey": 2.5, "Football": 3}.get(sport, 2)
            if exp_dt:
                kickoff_dt = exp_dt - timedelta(hours=duration_hours)

        sort_dt = game_date or (close_dt.date() if close_dt else None)

        # Build outcomes (limit to 5 for speed)
        outcomes = []
        for mk in mkts[:5]:
            label = str(mk.get("yes_sub_title") or "").strip() or str(mk.get("ticker", "")).split("-")[-1]
            try:
                yf = float(mk.get("yes_bid_dollars") or mk.get("yes_bid", 0) / 100)
                nf = float(mk.get("no_bid_dollars") or mk.get("no_bid", 0) / 100)
                outcomes.append((
                    label[:35],
                    f"{int(round(yf*100))}%",
                    f"{int(round(yf*100))}¢",
                    f"{int(round(nf*100))}¢"
                ))
            except:
                outcomes.append((label[:35], "—", "—", "—"))

        display_dt = fmt_date(kickoff_dt) if kickoff_dt else ""
        return sort_dt, game_date, kickoff_dt, display_dt, outcomes

    # Apply once and explode columns
    processed = df.apply(extract_row, axis=1, result_type="expand")
    df = df.copy()
    df[["_sort_dt", "_game_date", "_kickoff_dt", "_display_dt", "_outcomes"]] = processed

    return df

# ====================== Main App ======================
st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

# Controls
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

# Date filters (simplified)
date_mode = st.selectbox("", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")
include_no_date = st.toggle("Include undated", value=True)

if date_mode == "Custom":
    dc1, dc2 = st.columns(2)
    with dc1: d_start = st.date_input("From", value=date.today())
    with dc2: d_end = st.date_input("To", value=date.today() + timedelta(days=7))
else:
    today = date.today()
    d_start = d_end = today if date_mode == "Today" else (today if date_mode == "This week" else None)

with st.spinner("Loading & processing markets..."):
    raw_df = fetch_all()
    if raw_df.empty:
        st.stop()

    df = process_markets(raw_df)

# ====================== Filtering (vectorized where possible) ======================
filtered = df.copy()

# Date filter
if date_mode != "All dates" and d_start and d_end:
    def is_in_date_range(row):
        kdt = row.get("_kickoff_dt")
        if kdt is not None and not pd.isna(kdt):
            try:
                kd = kdt.date() if hasattr(kdt, "date") else kdt
                return d_start <= kd <= d_end
            except:
                return False
        return include_no_date
    filtered = filtered[filtered.apply(is_in_date_range, axis=1)]

# Search filter
if search:
    s = search.lower()
    mask = (
        filtered["title"].str.lower().str.contains(s, na=False) |
        filtered["event_ticker"].str.lower().str.contains(s, na=False) |
        filtered["category"].str.lower().str.contains(s, na=False)
    )
    filtered = filtered[mask]

# Sorting
if sort_by != "Default":
    asc = sort_by == "Earliest first"
    filtered = filtered.copy()
    filtered["_sk"] = filtered["_sort_dt"].apply(lambda d: d.isoformat() if d else "9999-12-31")
    dated = filtered[filtered["_sk"] != "9999-12-31"].sort_values("_sk", ascending=asc)
    undated = filtered[filtered["_sk"] == "9999-12-31"]
    filtered = pd.concat([dated, undated]).drop(columns=["_sk"])

# ====================== Render Cards (same beautiful HTML, but limited initially) ======================
def render_cards(data, max_cards=80):
    if data.empty:
        st.markdown('<div class="empty-state">No markets found.</div>', unsafe_allow_html=True)
        return

    data = data.head(max_cards)  # Prevent huge HTML on first load

    html = '<div class="card-grid">'
    for _, row in data.iterrows():
        try:
            ticker = str(row.get("event_ticker", "")).upper()
            cat = str(row.get("category", "Other"))
            title = str(row.get("title", ""))[:90]
            sport = str(row.get("_sport", ""))
            base_ic, pill = CAT_META.get(cat, ("📊", "pill-default"))
            icon = SPORT_ICONS.get(sport, base_ic) if sport else base_ic
            label = (sport or cat)[:16]
            dt = str(row.get("_display_dt", "Open"))
            outcomes = row.get("_outcomes") or []

            series_lower = str(row.get("series_ticker", "")).lower()
            kalshi_url = f"https://kalshi.com/markets/{series_lower}/{series_lower.replace('kx','')}/{ticker.lower()}" if series_lower else ""

            link_html = f'<a class="ticker-link" href="{kalshi_url}" target="_blank">{ticker}</a>' if kalshi_url else f'<span class="ticker-text">{ticker}</span>'

            odds_html = ""
            for olabel, ochance, oyes, ono in outcomes:
                odds_html += f'''
                <div class="outcome-row">
                    <div class="outcome-label">{olabel}</div>
                    <div class="outcome-chance">{ochance}</div>
                    <div class="outcome-odds">
                        <div class="odds-yes"><div class="odds-label">YES</div><div class="odds-price-yes">{oyes}</div></div>
                        <div class="odds-no"><div class="odds-label">NO</div><div class="odds-price-no">{ono}</div></div>
                    </div>
                </div>'''

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

# ====================== Category / Sports Navigation (unchanged logic) ======================
# ... keep your entire present_cats, top_tabs, Sports sidebar logic, filter_data, etc. exactly as before ...

# For the "All" and category tabs, just call render_cards(filtered) or the filtered view

st.markdown("<hr><p style='text-align:center;color:#1f2937;font-size:11px;'>KALSHI TERMINAL · CACHED 15 MIN · NOT FINANCIAL ADVICE</p>", unsafe_allow_html=True)
