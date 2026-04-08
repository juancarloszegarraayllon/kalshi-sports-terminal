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
    # Use Unix timestamps (integers)
    now = int(datetime.utcnow().timestamp())
    future = now + (7 * 24 * 60 * 60) 

    try:
        response = client.get_markets(
            limit=1000, 
            status="open",
            min_close_ts=now,
            max_close_ts=future
        )
        data = response.to_dict().get("markets", [])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # 1. Broader Identification Logic
    # In 2026, most sports tickers start with these prefixes
    sport_codes = ('NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'UFC', 'KX')
    
    # Identify sports using ticker or title keywords
    is_sports = (
        df['ticker'].str.startswith(sport_codes, na=False) | 
        df['title'].str.contains('vs|score|win|points', case=False, na=False)
    )
    
    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # 2. Defensive Processing (Creates the columns and handles missing data)
    for frame in [df_sports, df_other]:
        if not frame.empty:
            # Use new 2026 fixed-point dollar fields if available
            if 'yes_ask_dollars' in frame.columns:
                frame["Price"] = frame["yes_ask_dollars"].apply(lambda x: f"${float(x):.2f}" if pd.notnull(x) else "N/A")
            elif 'yes_ask' in frame.columns:
                frame["Price"] = frame["yes_ask"].apply(lambda x: f"{int(x)}¢" if pd.notnull(x) else "N/A")
            else:
                frame["Price"] = "N/A"
            
            if 'close_time' in frame.columns:
                frame["Ends (UTC)"] = pd.to_datetime(frame["close_time"]).dt.strftime('%m/%d %H:%M')
            else:
                frame["Ends (UTC)"] = "N/A"

    # --- UI Layout ---
    tab1, tab2 = st.tabs(["🏆 Sports", "📈 All Other"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports found for the next 7 days. Check the 'All Other' tab.")
        else:
            # ONLY select columns that we are sure exist now
            cols_to_show = [c for c in ["title", "Price", "Ends (UTC)"] if c in df_sports.columns]
            st.dataframe(df_sports[cols_to_show], use_container_width=True, hide_index=True)

    with tab2:
        if df_other.empty:
            st.info("No other markets found.")
        else:
            cols_to_show = [c for c in ["title", "Price", "Ends (UTC)"] if c in df_other.columns]
            st.dataframe(df_other[cols_to_show], use_container_width=True, hide_index=True)
else:
    st.info("No active markets found.")
