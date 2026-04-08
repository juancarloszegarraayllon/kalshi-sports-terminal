import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

# --- Page Configuration ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide")
st.title("🏀 Kalshi Sports Markets")

# --- Load API secrets from Streamlit ---
# These must be set in your Streamlit Cloud "Secrets" dashboard
try:
    api_key_id = st.secrets["KALSHI_API_KEY_ID"]
    private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]
except KeyError:
    st.error("Missing Secrets! Please add KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY to Streamlit Secrets.")
    st.stop()

# --- Write private key to temporary file for SDK ---
# The Kalshi SDK requires a file path for the RSA key
with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
    f.write(private_key_str)
    private_key_path = f.name

# --- Initialize Kalshi client ---
try:
    config = Configuration()
    config.api_key_id = api_key_id
    config.private_key_pem_path = private_key_path
    client = KalshiClient(config)
    st.sidebar.success("✅ Kalshi API Connected")
except Exception as e:
    st.error(f"Error initializing Kalshi client: {e}")
    st.stop()

# --- Function to fetch sports markets ---
@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_sports_markets():
    # Widening the window to 7 days to capture upcoming games
    now = datetime.utcnow()
    now_ts = int(now.timestamp())
    seven_days_later_ts = int((now + timedelta(days=7)).timestamp())

    try:
        # Fetching open markets using Unix timestamps
        response = client.get_markets(
            limit=100,
            status="open",
            min_close_ts=now_ts,
            max_close_ts=seven_days_later_ts
        )
    except ApiException as e:
        st.error(f"Kalshi API Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected connection error: {e}")
        return pd.DataFrame()

    markets = response.to_dict().get("markets", [])
    if not markets:
        return pd.DataFrame()

    df = pd.DataFrame(markets)

    # Reliable filtering: Look for 'Sports' in category or specific keywords in title
    sports_keywords = ["NBA", "NFL", "MLB", "Soccer", "Football", "Basketball", "Tennis", "NHL"]
    
    # Check if 'category' column exists (SDK structure can vary)
    if "category" in df.columns:
        df_sports = df[
            (df["category"].str.contains("Sports", case=False, na=False)) | 
            (df["title"].str.contains("|".join(sports_keywords), case=False, na=False))
        ].copy()
    else:
        df_sports = df[df["title"].str.contains("|".join(sports_keywords), case=False, na=False)].copy()

    # Calculate readable probability percentages
    if not df_sports.empty:
        if "yes_ask" in df_sports.columns:
            df_sports["YES %"] = df_sports["yes_ask"].astype(float) / 100
        if "no_ask" in df_sports.columns:
            df_sports["NO %"] = df_sports["no_ask"].astype(float) / 100
            
        # Format the time for better readability
        if "close_time" in df_sports.columns:
            df_sports["Closes (UTC)"] = pd.to_datetime(df_sports["close_time"]).dt.strftime('%Y-%m-%d %H:%M')

    return df_sports

# --- App Layout & Execution ---
st.write("### Live Betting Markets")
st.info("Showing open sports markets closing within the next 7 days.")

with st.spinner("Syncing with Kalshi Exchange..."):
    df_sports = fetch_sports_markets()

if df_sports.empty:
    st.warning("No sports markets found for the next 7 days. Check back closer to game time!")
else:
    # Select specific columns to display to keep the UI clean
    display_cols = ["title", "Closes (UTC)", "YES %", "NO %"]
    # Filter only for columns that actually exist in the dataframe
    existing_cols = [c for c in display_cols if c in df_sports.columns]
    
    st.dataframe(
        df_sports[existing_cols].sort_values(by="Closes (UTC)" if "Closes (UTC)" in df_sports.columns else "title"),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.caption("Data provided by Kalshi API. Probabilities based on current 'Ask' prices.")
