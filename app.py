import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timezone, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")
st.title("🏀 Kalshi Sports Terminal")

# --- API Setup ---
api_key_id = st.secrets["KALSHI_API_KEY_ID"]
private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]

with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
    f.write(private_key_str)
    private_key_path = f.name

try:
    config = Configuration()
    config.api_key_id = api_key_id
    config.private_key_pem_path = private_key_path
    client = KalshiClient(config)
except Exception as e:
    st.error(f"Init Error: {e}")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("🎯 Market Filters")
min_prob = st.sidebar.slider("Min Probability (%)", 0, 100, 0)
search_query = st.sidebar.text_input("Search Teams", "")
selected_date = st.sidebar.date_input("Select Date", datetime.utcnow().date())

# --- Fetch Markets (All Open) ---
@st.cache_data(ttl=300)
def fetch_markets():
    try:
        response = client.get_markets(limit=1000, status="open")
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # --- Sports Filtering ---
    sport_prefixes = ('KX', 'NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN')
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df['event_ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|score|points|win', case=False, na=False)
    )
    is_macro = df['title'].str.contains("inflation|cpi|rate|fed|gdp|election", case=False, na=False)
    df_sports = df[is_sports & ~is_macro].copy()

    if not df_sports.empty:
        # --- Probability Column ---
        if 'yes_ask_dollars' in df_sports.columns:
            df_sports["Prob %"] = (pd.to_numeric(df_sports["yes_ask_dollars"]) * 100).fillna(0).astype(int)
        elif 'yes_ask' in df_sports.columns:
            df_sports["Prob %"] = pd.to_numeric(df_sports["yes_ask"]).fillna(0).astype(int)

        # --- Event/Close Time ---
        df_sports["close_time_dt"] = pd.to_datetime(df_sports["close_time"], unit='s', utc=True)
        df_sports["Ends (UTC)"] = df_sports["close_time_dt"].dt.strftime('%m/%d %H:%M')

        # --- Flag Markets Happening Today ---
        df_sports["Today"] = df_sports["close_time_dt"].dt.date == selected_date

        # --- Sidebar Filters ---
        if search_query:
            df_sports = df_sports[df_sports['title'].str.contains(search_query, case=False, na=False)]
        df_sports = df_sports[df_sports["Prob %"] >= min_prob]

        # --- Highlight Imminent Matches ---
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        def highlight_row(row):
            delta = row["close_time_dt"] - now
            if row["Today"]:
                if delta <= timedelta(hours=2):
                    return ['background-color: #a0ffa0']*len(row)  # Green: imminent today
                elif delta <= timedelta(hours=6):
                    return ['background-color: #fff8a0']*len(row)  # Yellow: upcoming today
            return ['']*len(row)

    # --- Display ---
    if df_sports.empty:
        st.warning("No sports matches found for the selected filters.")
    else:
        st.write(f"Showing **{len(df_sports)}** sports markets (green/yellow = happening today).")
        display_cols = ["title", "Prob %", "Ends (UTC)", "ticker", "Today"]
        st.dataframe(
            df_sports[display_cols].sort_values("close_time_dt").style.apply(highlight_row, axis=1),
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("No active markets found.")
