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
    st.error(f"Initialization Error: {e}")
    st.stop()

@st.cache_data(ttl=300)
def fetch_markets():
    # Use Unix timestamps (integers) to satisfy SDK validation
    now = int(datetime.utcnow().timestamp())
    future = now + (7 * 24 * 60 * 60) # Look 7 days ahead

    try:
        # Replaced start_time_min with min_close_ts (integer only)
        response = client.get_markets(
            limit=1000, 
            status="open",
            min_close_ts=now,
            max_close_ts=future
        )
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # --- Advanced Sport Identification ---
    # Kalshi 2026 uses tickers like NBA, MLB, NHL, or SOC (Soccer)
    sport_codes = ('NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'UFC', 'KX')
    
    is_sports = (
        df['ticker'].str.startswith(sport_codes, na=False) | 
        df['event_ticker'].str.startswith(sport_codes, na=False) |
        df['title'].str.contains('vs|score|win|points', case=False, na=False)
    )
    
    if "category" in df.columns:
        is_sports = is_sports | (df["category"].str.contains("Sports", case=False, na=False))

    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # --- Formatting for Display ---
    for frame in [df_sports, df_other]:
        if not frame.empty:
            if 'yes_ask' in frame.columns:
                frame["Price"] = frame["yes_ask"].apply(lambda x: f"{int(x)}¢")
            if 'close_time' in frame.columns:
                frame["Ends (UTC)"] = pd.to_datetime(frame["close_time"]).dt.strftime('%m/%d %H:%M')

    tab1, tab2 = st.tabs(["🏆 Sports", "📈 All Other"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports found for the next 7 days.")
        else:
            st.dataframe(df_sports[["title", "Price", "Ends (UTC)"]], use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(df_other[["title", "Price", "Ends (UTC)"]], use_container_width=True, hide_index=True)
else:
    st.info("No active markets found.")
