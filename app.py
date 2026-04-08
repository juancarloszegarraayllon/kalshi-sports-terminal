import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide")
st.title("🏀 Kalshi Sports & Featured Markets")

# --- Load Secrets ---
api_key_id = st.secrets["KALSHI_API_KEY_ID"]
private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]

# --- API Setup ---
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

@st.cache_data(ttl=300)
def fetch_all_markets():
    # Use a wider window (7 days) to see upcoming games
    now = int(datetime.utcnow().timestamp())
    future = now + (7 * 24 * 60 * 60)

    try:
        response = client.get_markets(
            limit=200, # Increased limit to ensure we see sports
            status="open",
            min_close_ts=now,
            max_close_ts=future
        )
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_all_markets()

if not df.empty:
    # 1. Expanded Keywords
    sports_list = [
        "NBA", "NFL", "MLB", "NHL", "Soccer", "Tennis", "UFC", "Golf", 
        "Lakers", "Warriors", "Dodgers", "Yankees", "Inter Miami"
    ]
    
    # 2. Advanced Filtering
    # Check category column OR title for any sports names
    is_sports = df["title"].str.contains("|".join(sports_list), case=False, na=False)
    if "category" in df.columns:
        is_sports = is_sports | (df["category"].str.contains("Sports", case=False, na=False))

    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # --- UI Layout ---
    tab1, tab2 = st.tabs(["🏆 Sports Markets", "📈 All Other Markets"])

    with tab1:
        if df_sports.empty:
            st.warning("No specific sports matches found. Showing 'Other' markets in the second tab.")
        else:
            # Clean up percentages for display
            if "yes_ask" in df_sports.columns:
                df_sports["Prob %"] = (df_sports["yes_ask"] / 1).astype(int).astype(str) + "%"
            st.dataframe(df_sports[["title", "Prob %", "close_time"]], use_container_width=True)

    with tab2:
        st.write("These are non-sports markets (like Argentina Inflation) currently open:")
        st.dataframe(df_other[["title", "close_time"]], use_container_width=True)

else:
    st.info("No markets found. Verify your API credentials.")
