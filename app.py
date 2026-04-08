import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient

st.set_page_config(page_title="Kalshi Sports Board", layout="wide", page_icon="🏀")
st.title("🏟️ Today's Full Sports Board")

# --- API Initialization ---
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

# --- Sidebar Controls ---
st.sidebar.header("🎯 Filters")
# Codes like KXNBA, KXMLB, and KXNHL are standard in April 2026
leagues_map = {
    "NBA": "NBA",
    "MLB": "MLB",
    "NHL": "NHL",
    "Soccer": "SOC",
    "NFL": "NFL",
    "Tennis": "TEN"
}
selected_leagues = st.sidebar.multiselect("Select Leagues", options=list(leagues_map.keys()), default=["NBA", "MLB"])
selected_codes = [leagues_map[l] for l in selected_leagues]

@st.cache_data(ttl=60)
def fetch_unlimited_markets():
    now_ts = int(datetime.utcnow().timestamp())
    # 24-hour window for the current daily slate
    tomorrow_ts = now_ts + (24 * 60 * 60)
    
    try:
        response = client.get_markets(
            limit=1000, 
            status="open", 
            min_close_ts=now_ts, 
            max_close_ts=tomorrow_ts
        )
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

df = fetch_unlimited_markets()

if not df.empty:
    # --- FIX: USE CONTAINS INSTEAD OF STARTSWITH ---
    # This ensures KXNBA or 2026NBA both get caught
    search_pattern = "|".join(selected_codes)
    df_sports = df[
        (df['event_ticker'].str.contains(search_pattern, case=False, na=False)) |
        (df['ticker'].str.contains(search_pattern, case=False, na=False))
    ].copy()

    if not df_sports.empty:
        # Use the 2026 _dollars field
        if 'yes_ask_dollars' in df_sports.columns:
            df_sports["Win Prob"] = df_sports["yes_ask_dollars"].apply(lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) else "N/A")
        
        df_sports["Game Start (UTC)"] = pd.to_datetime(df_sports["close_time"]).dt.strftime('%H:%M')
        
        st.write(f"### Found {len(df_sports)} Matches")
        
        # Displaying grouped by your selected Leagues
        for league_name in selected_leagues:
            code = leagues_map[league_name]
            league_df = df_sports[df_sports['event_ticker'].str.contains(code, case=False, na
