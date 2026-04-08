import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Config ---
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
# April 2026 update: Most sports now use 'KX' prefixes
target_leagues = st.sidebar.multiselect(
    "Select Leagues", 
    ["KXNBA", "KXMLB", "KXNHL", "KXSOC", "KXNFL", "KXTEN"], 
    default=["KXNBA", "KXMLB"]
)

@st.cache_data(ttl=60)
def fetch_unlimited_markets():
    now_ts = int(datetime.utcnow().timestamp())
    # Looking 24 hours ahead for today's specific slate
    tomorrow_ts = now_ts + (24 * 60 * 60)
    
    try:
        # Fetching 1000 markets to ensure nothing is missed
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
    # --- RELIABLE 2026 FILTERING ---
    # We filter by event_ticker prefix (e.g. 'KXNBA') which is immutable
    df_sports = df[df['event_ticker'].str.startswith(tuple(target_leagues), na=False)].copy()

    if not df_sports.empty:
        # Processing Prices: Using the mandatory 2026 '_dollars' fields
        if 'yes_ask_dollars' in df_sports.columns:
            df_sports["Win Prob"] = df_sports["yes_ask_dollars"].apply(lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) else "N/A")
        
        # Formatting Time
        df_sports["Game Start (UTC)"] = pd.to_datetime(df_sports["close_time"]).dt.strftime('%H:%M')
        
        # UI Display
        st.write(f"### Found {len(df_sports)} Matches for Today")
        
        # Displaying grouped by League
        for league in target_leagues:
            league_df = df_sports[df_sports['event_ticker'].str.startswith(league)]
            if not league_df.empty:
                with st.expander(f"📅 {league} Schedule", expanded=True):
                    st.dataframe(
                        league_df[["title", "Win Prob", "Game Start (UTC)", "ticker"]].sort_values("Game Start (UTC)"),
                        use_container_width=True,
                        hide_index=True
                    )
    else:
        st.warning("No open markets found for the selected leagues in the next 24 hours.")
        st.info("💡 Try selecting more leagues in the sidebar or checking if games have already started (Status: Closed).")
else:
    st.info("📡 Connecting to Kalshi exchange...")
