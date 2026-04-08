import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")
st.title("🏀 Kalshi Sports Terminal")

# --- Load Secrets & API Setup ---
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

# 1. League Filter
leagues = {
    "NBA": "NBA",
    "MLB": "MLB",
    "NHL": "NHL",
    "NFL": "NFL",
    "Soccer": "SOC",
    "Tennis": "TEN"
}
selected_leagues = st.sidebar.multiselect("Select Leagues", options=list(leagues.keys()), default=list(leagues.keys()))
selected_prefixes = [leagues[l] for l in selected_leagues]

# 2. Probability Filter
min_prob = st.sidebar.slider("Minimum 'YES' Probability (%)", 0, 100, 0)

# 3. Search Bar
search_query = st.sidebar.text_input("Search Teams (e.g. Lakers)", "")

@st.cache_data(ttl=300)
def fetch_markets():
    now = int(datetime.utcnow().timestamp())
    future = now + (7 * 24 * 60 * 60) 
    try:
        response = client.get_markets(limit=1000, status="open", min_close_ts=now, max_close_ts=future)
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # --- Filter Logic ---
    # A. Ticker/League Filter
    is_league = df['ticker'].str.startswith(tuple(selected_prefixes), na=False) | \
                df['event_ticker'].str.startswith(tuple(selected_prefixes), na=False)
    
    # B. Text Search Filter
    is_search = df['title'].str.contains(search_query, case=False, na=False) if search_query else True
    
    # C. Exclusion Filter (Removes Inflation/Economics from Sports tab)
    not_sports = df['title'].str.contains("inflation|cpi|rate|fed|biden|trump", case=False, na=False)

    df_sports = df[is_league & is_search & ~not_sports].copy()
    
    # --- Formatting & Probability Filter ---
    if not df_sports.empty:
        # Use 2026 dollar fields or standard yes_ask
        col = "yes_ask_dollars" if "yes_ask_dollars" in df_sports.columns else "yes_ask"
        
        # Calculate numeric probability for filtering
        df_sports["prob_val"] = pd.to_numeric(df_sports[col], errors='coerce')
        # On Kalshi, yes_ask is usually 1-99 (cents) or 0.01-0.99 (dollars)
        if col == "yes_ask":
            df_sports["Prob %"] = df_sports["prob_val"]
        else:
            df_sports["Prob %"] = (df_sports["prob_val"] * 100).fillna(0).astype(int)
        
        # Apply the Sidebar Probability Slider
        df_sports = df_sports[df_sports["Prob %"] >= min_prob]
        
        # Final formatting
        df_sports["Ends (UTC)"] = pd.to_datetime(df_sports["close_time"]).dt.strftime('%m/%d %H:%M')
        df_sports["Price"] = df_sports["Prob %"].apply(lambda x: f"{x}%")

    # --- UI ---
    if df_sports.empty:
        st.warning("No sports matches found with the current filters.")
    else:
        st.write(f"Showing **{len(df_sports)}** active markets")
        cols = ["title", "Price", "Ends (UTC)", "ticker"]
        st.dataframe(df_sports[cols].sort_values("Prob %", ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("No active markets found.")
