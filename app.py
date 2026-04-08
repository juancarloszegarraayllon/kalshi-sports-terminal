import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

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

@st.cache_data(ttl=300)
def fetch_markets():
    now = int(datetime.utcnow().timestamp())
    future = now + (3 * 24 * 60 * 60) # 3 days is plenty for daily sports
    try:
        response = client.get_markets(limit=1000, status="open", min_close_ts=now, max_close_ts=future)
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # --- 2026 Ticker Logic ---
    # Most sports now use prefixes starting with KX (e.g., KXNBA, KXMLB)
    sport_prefixes = ('KX', 'NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN')
    
    # 1. Broad Sports Filter
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df['event_ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|score|points|win', case=False, na=False)
    )
    
    # 2. Hard Exclusion for Macro/Economics (like Argentina Inflation)
    is_macro = df['title'].str.contains("inflation|cpi|rate|fed|gdp|election", case=False, na=False)
    
    df_sports = df[is_sports & ~is_macro].copy()

    # --- Data Processing ---
    if not df_sports.empty:
        # Use newer dollar-denominated fields if available, otherwise cents
        if 'yes_ask_dollars' in df_sports.columns:
            df_sports["Prob %"] = (pd.to_numeric(df_sports["yes_ask_dollars"]) * 100).fillna(0).astype(int)
        elif 'yes_ask' in df_sports.columns:
            df_sports["Prob %"] = pd.to_numeric(df_sports["yes_ask"]).fillna(0).astype(int)
        
        # Apply Sidebar Filters
        if search_query:
            df_sports = df_sports[df_sports['title'].str.contains(search_query, case=False, na=False)]
        df_sports = df_sports[df_sports["Prob %"] >= min_prob]

        # Final Formatting
        df_sports["Ends (UTC)"] = pd.to_datetime(df_sports["close_time"]).dt.strftime('%m/%d %H:%M')
        df_sports["Price"] = df_sports["Prob %"].astype(str) + "%"

    # --- Display ---
    if df_sports.empty:
        st.warning("No sports matches found. Ensure your filters aren't too restrictive.")
    else:
        st.write(f"Showing **{len(df_sports)}** live sports markets.")
        # Sorting by title makes it easier to find specific games
        display_cols = ["title", "Price", "Ends (UTC)", "ticker"]
        st.dataframe(df_sports[display_cols].sort_values("title"), use_container_width=True, hide_index=True)

else:
    st.info("No active markets found.")
