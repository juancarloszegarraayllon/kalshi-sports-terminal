import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import date, timedelta, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

UTC = timezone.utc

# -------------------------
# CATEGORIES (YOUR ORIGINAL)
# -------------------------

TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_TAGS = {
    "Economics":["Fed","Inflation","GDP","Jobs","Housing"],
    "Crypto":["BTC","ETH","SOL"],
    "Companies":["IPOs","CEOs","Layoffs"],
    "Entertainment":["Movies","Music","Awards"],
    "Climate and Weather":["Hurricanes","Temperature"],
    "Science and Technology":["AI","Space"],
    "Health":["Diseases"],
    "Mentions":["Earnings","Sports"]
}

SPORT_PREFIX = {
    "Soccer": ["KX"],
    "Basketball": ["KXNBA"],
    "Baseball": ["KXMLB"],
    "Football": ["KXNFL"],
    "Tennis": ["KXATP"],
}

# -------------------------
# UTIL
# -------------------------

def safe_date(val):
    try:
        ts = pd.to_datetime(val, utc=True)
        return ts.to_pydatetime().date()
    except:
        return None

def fmt_pct(v):
    try:
        f = float(v)
        return f"{int(round(f*100)) if f <= 1 else int(round(f))}%"
    except:
        return "—"

def detect_sport(series):
    if not isinstance(series, str):
        return ""
    for sport, prefixes in SPORT_PREFIX.items():
        if any(series.startswith(p) for p in prefixes):
            return sport
    return ""

# Soccer competitions (simplified but working)
def get_soccer_comp(series):
    s = str(series).upper()
    if "EPL" in s or "PREMIER" in s:
        return "EPL"
    if "UCL" in s:
        return "Champions League"
    if "LALIGA" in s:
        return "La Liga"
    if "SERIEA" in s:
        return "Serie A"
    if "BUNDES" in s:
        return "Bundesliga"
    return "Other"

# -------------------------
# CLIENT
# -------------------------

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

# -------------------------
# FETCH (FIXED)
# -------------------------

@st.cache_data(ttl=600)
def fetch_data():
    events = []
    cursor = None

    for _ in range(25):
        for attempt in range(3):
            try:
                resp_raw = client.get_events(
                    limit=200,
                    status="open",
                    with_nested_markets=True,
                    cursor=cursor
                )

                try:
                    resp = resp_raw.to_dict()
                except:
                    resp = resp_raw if isinstance(resp_raw, dict) else {}

                batch = resp.get("events", [])
                if not batch:
                    return pd.DataFrame(events)

                events.extend(batch)
                cursor = resp.get("cursor") or resp.get("next_cursor")

                if not cursor:
                    return pd.DataFrame(events)

                time.sleep(0.2)
                break

            except Exception as e:
                if "429" in str(e):
                    time.sleep(2 + attempt)
                else:
                    return pd.DataFrame(events)

    return pd.DataFrame(events)

# -------------------------
# PROCESS DATA
# -------------------------

def process_df(df):
    if df.empty:
        return df

    df = pd.json_normalize(df)

    df["title"] = df.get("title", "").astype(str)
    df["category"] = df.get("category", "Other").astype(str)
    df["series_ticker"] = df.get("series_ticker", "").astype(str)

    df["_sport"] = df["series_ticker"].apply(detect_sport)
    df["_is_sport"] = df["_sport"] != ""

    df["_soccer_comp"] = df.apply(
        lambda r: get_soccer_comp(r["series_ticker"]) if r["_sport"] == "Soccer" else "",
        axis=1
    )

    def extract(row):
        mkts = row.get("markets", [])
        if not isinstance(mkts, list) or not mkts:
            return "—", "—"

        m = mkts[0] if isinstance(mkts[0], dict) else {}

        yes = fmt_pct(m.get("yes_bid_dollars") or m.get("yes_bid") or m.get("yes_ask"))
        no  = fmt_pct(m.get("no_bid_dollars") or m.get("no_bid") or m.get("no_ask"))

        return yes, no

    odds = df.apply(extract, axis=1, result_type="expand")
    df["_yes"] = odds[0]
    df["_no"] = odds[1]

    return df

# -------------------------
# UI
# -------------------------

st.title("📡 Kalshi Markets Terminal")

raw_df = fetch_data()
df = process_df(raw_df)

if df.empty:
    st.error("No data loaded")
    st.stop()

# -------------------------
# SEARCH
# -------------------------

search = st.text_input("🔍 Search")

if search:
    s = search.lower()
    df = df[
        df["title"].str.lower().str.contains(s, na=False) |
        df["category"].str.lower().str.contains(s, na=False)
    ]

# -------------------------
# RENDER
# -------------------------

def render_cards(data):
    if data.empty:
        st.write("No markets")
        return

    for _, row in data.iterrows():
        st.markdown(f"""
        **{row['title']}**  
        YES: {row['_yes']} | NO: {row['_no']}
        """)

def render_sports(df):
    sports = sorted(df["_sport"].unique())
    tabs = st.tabs(["All"] + sports)

    for i, tab in enumerate(tabs):
        with tab:
            if i == 0:
                render_cards(df)
            else:
                sport = sports[i-1]
                sdf = df[df["_sport"] == sport]

                if sport == "Soccer":
                    comps = sdf["_soccer_comp"].unique()
                    ctabs = st.tabs(["All"] + list(comps))

                    for j, ctab in enumerate(ctabs):
                        with ctab:
                            if j == 0:
                                render_cards(sdf)
                            else:
                                render_cards(sdf[sdf["_soccer_comp"] == comps[j-1]])
                else:
                    render_cards(sdf)

def render_category(df, cat):
    cdf = df[df["category"] == cat]

    tags = CAT_TAGS.get(cat, [])

    if not tags:
        render_cards(cdf)
        return

    tabs = st.tabs(["All"] + tags)

    for i, tab in enumerate(tabs):
        with tab:
            if i == 0:
                render_cards(cdf)
            else:
                tag = tags[i-1]
                render_cards(cdf[cdf["title"].str.contains(tag, case=False, na=False)])

# -------------------------
# MAIN TABS
# -------------------------

tabs = st.tabs(["All"] + TOP_CATS)

for i, tab in enumerate(tabs):
    with tab:
        if i == 0:
            render_cards(df)
        else:
            cat = TOP_CATS[i-1]

            if cat == "Sports":
                render_sports(df[df["_is_sport"]])
            else:
                render_category(df, cat)
