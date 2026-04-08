import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide")
st.title("🏀 Kalshi Sports & Featured Markets")

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

@st.cache_data(ttl=300)
def fetch_all_markets():
    now = int(datetime.utcnow().timestamp())
    # Wide window to catch the whole week of sports
    future = now + (7 * 24 * 60 * 60)

    try:
        # Increase limit to 1000 to catch all active markets
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

df = fetch_all_markets()

if not df.empty:
    # --- Advanced Sport Filtering ---
    # Kalshi usually prefixes sports tickers with league names or specific codes
    sport_prefixes = ('NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'UFC', 'KX')
    
    # Identify sports by Ticker prefix OR Category OR common Title keywords
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) | 
        df['event_ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|score|points|win', case=False, na=False)
    )
    
    # Also check the explicit category field if it exists
    if "category" in df.columns:
        is_sports = is_sports | (df["category"].str.contains("Sports", case=False, na=False))

    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # --- Defensive Data Processing ---
    for target_df in [df_sports, df_other]:
        if not target_df.empty:
            # Calculate Probability from the 'yes_ask' (price in cents)
            if 'yes_ask' in target_df.columns:
                target_df["Prob %"] = target_df["yes_ask"].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "0%")
            else:
                target_df["Prob %"] = "N/A"
            
            # Format Closing Time
            if 'close_time' in target_df.columns:
                target_df["Ends (UTC)"] = pd.to_datetime(target_df["close_time"]).dt.strftime('%m/%d %H:%M')
            else:
                target_df["Ends (UTC)"] = "N/A"

    # --- UI Layout ---
    tab1, tab2 = st.tabs(["🏆 Sports Markets", "📈 Non-Sports Markets"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports matches found. Try checking the 'Non-Sports' tab to see what's available.")
        else:
            # Display sorted by closing time
            cols = ["title", "Prob %", "Ends (UTC)", "ticker"]
            st.dataframe(df_sports[cols].sort_values("Ends (UTC)"), use_container_width=True, hide_index=True)

    with tab2:
        if df_other.empty:
            st.info("No other markets found.")
        else:
            st.dataframe(df_other[["title", "Prob %", "Ends (UTC)"]], use_container_width=True, hide_index=True)
else:
    st.info("Connecting to Kalshi... No markets currently found.")
