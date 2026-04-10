import streamlit as st
import pandas as pd
import time
from datetime import date, timedelta, timezone
import re

st.set_page_config(page_title="OddsIQ", layout="wide", page_icon="")

# ====================== CSS (unchanged - you can keep it) ======================
# ... [your entire <style> block] ...

UTC = timezone.utc

# ====================== CATEGORY & SPORT DATA (unchanged) ======================
# ... keep all your TOP_CATS, CAT_META, CAT_TAGS, SERIES_SPORT, SOCCER_COMP, SPORT_SUBTABS etc. ...

# ====================== OPTIMIZED HELPERS ======================

@st.cache_resource
def get_client():
    from kalshi_python_sync import Configuration, KalshiClient
    key_id = st.secrets["KALSHI_API_KEY_ID"]
    key_str = st.secrets["KALSHI_PRIVATE_KEY"]
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(key_str)
        pem = f.name
    
    cfg = Configuration()
    cfg.api_key_id = key_id
    cfg.private_key_pem_path = pem
    return KalshiClient(cfg)

def parse_game_date_from_ticker(event_ticker: str):
    """Fast regex-based date parser"""
    MONTHS = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
              "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
    try:
        parts = event_ticker.split("-")
        if len(parts) < 2:
            return None
        seg = parts[1]
        m = re.match(r"(\d{2})([A-Z]{3})(\d{2})", seg)
        if not m:
            return None
        yy, mon, dd = m.group(1), m.group(2), m.group(3)
        return date(2000 + int(yy), MONTHS[mon], int(dd))
    except:
        return None

def safe_dt(val):
    if not val or val in ("", "NaT", "None", "nan"):
        return None
    try:
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().astimezone(UTC) if not pd.isna(ts) else None
    except:
        return None

# ====================== OPTIMIZED FETCHING ======================

@st.cache_data(ttl=900, show_spinner=False)  # 15 min cache instead of 30
def fetch_all_events():
    """Fetch events with minimal processing"""
    client = get_client()
    events = []
    cursor = None
    max_pages = 25  # reduced from 30

    progress = st.progress(0, text="Fetching markets from Kalshi...")

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

            progress.progress(min(0.95, (i+1)/max_pages), 
                            text=f"Loaded {len(events)} events...")

            if not cursor:
                break
            time.sleep(0.08)  # slightly gentler rate limit

        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            else:
                st.warning(f"API error: {e}")
                break

    progress.empty()
    return pd.DataFrame(events)

def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Heavy lifting done once and cached"""
    if df.empty:
        return df

    df = df.copy()

    # Basic cleaning
    df["category"] = df.get("category", "Other").fillna("Other").str.strip()
    df["_series"] = df.get("series_ticker", "").fillna("").str.upper()
    df["_sport"] = df["_series"].map(get_sport)  # vectorized map is faster than apply
    df["_is_sport"] = df["_sport"] != ""

    # Soccer competition
    df["_soccer_comp"] = df.apply(
        lambda r: SOCCER_COMP.get(r["_series"], "Other") if r["_sport"] == "Soccer" else "",
        axis=1
    )

    # --- Fast outcome + date extraction (vectorized where possible) ---
    def extract_row(row):
        markets = row.get("markets") or []
        if not markets:
            return None, None, None, None, None, []

        first = markets[0]
        event_ticker = str(row.get("event_ticker", ""))

        game_date = parse_game_date_from_ticker(event_ticker)
        close_dt = safe_dt(first.get("close_time"))
        exp_dt = safe_dt(first.get("expected_expiration_time"))

        # Kickoff estimation (only for sports with game_date)
        kickoff_dt = None
        if game_date and row["_sport"]:
            duration = {
                "Soccer": timedelta(hours=2),
                "Baseball": timedelta(hours=3),
                "Basketball": timedelta(hours=2, minutes=30),
                "Hockey": timedelta(hours=2, minutes=30),
                "Football": timedelta(hours=3),
            }.get(row["_sport"], timedelta(hours=2))

            if exp_dt:
                kickoff_dt = exp_dt - duration
            elif close_dt:
                kickoff_dt = close_dt - duration

        sort_dt = game_date or (close_dt.date() if close_dt else None)

        # Extract outcomes (limit to first 5)
        outcomes = []
        for m in markets[:5]:
            label = str(m.get("yes_sub_title") or "").strip()
            if not label:
                t = str(m.get("ticker", ""))
                label = t.rsplit("-", 1)[-1] if "-" in t else t

            yf = nf = None
            try:
                yd = m.get("yes_bid_dollars") or m.get("yes_bid")
                nd = m.get("no_bid_dollars") or m.get("no_bid")
                if yd is not None:
                    yf = float(yd) / 100 if yd > 1 else float(yd)
                if nd is not None:
                    nf = float(nd) / 100 if nd > 1 else float(nd)
            except:
                pass

            outcomes.append((
                label[:35],
                f"{int(round(yf*100))}% " if yf is not None else "—",
                f"{int(round(yf*100))}¢" if yf is not None else "—",
                f"{int(round(nf*100))}¢" if nf is not None else "—"
            ))

        return sort_dt, game_date, kickoff_dt, "", outcomes

    # Apply extraction
    extracted = df.apply(extract_row, axis=1, result_type="expand")
    df["_sort_dt"] = extracted[0]
    df["_game_date"] = extracted[1]
    df["_kickoff_dt"] = extracted[2]
    df["_begins"] = extracted[3]
    df["_outcomes"] = extracted[4]

    # Display date
    def fmt_kickoff(kdt):
        if not kdt:
            return ""
        try:
            return kdt.strftime("%b %d, %I:%M%p %Z").replace(" 0", " ")
        except:
            return ""

    df["_display_dt"] = df["_kickoff_dt"].apply(fmt_kickoff)

    return df

# ====================== MAIN APP ======================

st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-family:Helvetica,Arial,sans-serif;font-weight:800;margin-bottom:1rem;line-height:1.1;'>OddsIQ</div>", unsafe_allow_html=True)

# Controls
col1, col2, col3 = st.columns([3, 1.5, 1])
with col1:
    search = st.text_input("🔍 Search team, player, market…", "", label_visibility="collapsed")
with col2:
    sort_by = st.selectbox("Sort", ["Earliest first", "Latest first", "Default"], index=0, label_visibility="collapsed")
with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        fetch_all_events.clear()
        st.rerun()

# Date filter (simplified)
date_mode = st.selectbox("Date filter", ["All dates", "Today", "This week", "Custom"], label_visibility="collapsed")

if date_mode == "Custom":
    c1, c2 = st.columns(2)
    d_start = c1.date_input("From", value=date.today())
    d_end = c2.date_input("To", value=date.today() + timedelta(days=7))
else:
    d_start = d_end = None

# ====================== LOAD & PROCESS ======================
with st.spinner("Loading Kalshi markets..."):
    raw_df = fetch_all_events()

if raw_df.empty:
    st.error("Failed to load data from Kalshi.")
    st.stop()

# Preprocess once (this is cached)
df = preprocess_dataframe(raw_df)

# ====================== FILTERING ======================
filtered = df.copy()

# Date filtering
if date_mode != "All dates":
    today = date.today()
    if date_mode == "Today":
        d_start = d_end = today
    elif date_mode == "This week":
        d_start = today
        d_end = today + timedelta(days=6)

    def is_in_date_range(row):
        kdt = row.get("_kickoff_dt")
        if kdt and hasattr(kdt, "date"):
            return d_start <= kdt.date() <= d_end
        return True  # show undated if no date filter strict

    filtered = filtered[filtered.apply(is_in_date_range, axis=1)]

# Search
if search:
    s = search.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(s, na=False) |
        filtered["event_ticker"].str.lower().str.contains(s, na=False)
    ]

# Sorting
if sort_by != "Default":
    asc = sort_by == "Earliest first"
    filtered = filtered.sort_values("_sort_dt", ascending=asc, na_position='last')

# ====================== RENDERING ======================
# ... keep your render_cards() function (it's already quite efficient) ...

# Keep your tab + navigation logic for Sports / Categories

# Final render
if "Sports" in present_cats:   # your existing logic
    # ... your sport nav + cards ...
    pass
else:
    render_cards(filtered)

st.caption("KALSHI TERMINAL • Cached 15 min • Not financial advice")
