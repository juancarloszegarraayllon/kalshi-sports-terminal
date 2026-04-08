import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

st.set_page_config(page_title="Kalshi Sports Markets", layout="wide")
st.title("🏀 Kalshi Sports Markets – Today")

# --- Load API secrets from Streamlit ---
# Ensure these match the keys in your Streamlit Secrets dashboard
api_key_id = st.secrets["KALSHI_API_KEY_ID"]
private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]

# --- Write private key to temporary file for SDK ---
with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
    f.write(private_key_str)
    private_key_path = f.name

st.write(f"🔑 API Key loaded: {bool(api_key_id)}")
st.write(f"🔑 Private Key path ready: {bool(private_key_path)}")

# --- Initialize Kalshi client ---
try:
    config = Configuration()
    config.api_key_id = api_key_id
    config.private_key_pem_path = private_key_path
    client = KalshiClient(config)
    st.success("✅ Kalshi client initialized successfully!")
except Exception as e:
    st.error(f"Error initializing Kalshi client: {e}")
    st.stop()

# --- Function to fetch today's sports markets ---
@st.cache_data(ttl=60)
def fetch_sports_markets():
    # Calculate time range for today
    today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_utc = today_utc + timedelta(days=1)

    # The SDK requires Unix timestamps (integers) for the 'ts' parameters
    today_ts = int(today_utc.timestamp())
    tomorrow_ts = int(tomorrow_utc.timestamp())

    try:
        # Updated parameters to match the latest SDK version
        # start_time_min/max replaced with min_close_ts/max_close_ts
        response = client.get_markets(
            limit=100,
            status="open",
            min_close_ts=today_ts,
            max_close_ts=tomorrow_ts
        )
    except ApiException as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

    markets = response.to_dict().get("markets", [])
    if not markets:
        return pd.DataFrame()

    df = pd.DataFrame(markets)

    # Filter only sports markets
    sports_keywords = ["NBA", "NFL", "MLB", "Soccer", "Football", "Basketball", "Tennis"]
    df_sports = df[df["title"].str.contains("|".join(sports_keywords), case=False, na=False)]

    # Add YES/NO % if available
    if "yes_ask" in df_sports.columns:
        df_sports["YES %"] = df_sports["yes_ask"] / 100
    if "no_ask" in df_sports.columns:
        df_sports["NO %"] = df_sports["no_ask"] / 100

    return df_sports

# --- Display markets ---
st.write("🔄 Fetching today's sports markets from Kalshi...")
df_sports = fetch_sports_markets()

if df_sports.empty:
    st.info("No sports markets found today.")
else:
    # Displaying essential columns
    st.dataframe(df_sports[["title", "start_time", "YES %", "NO %"]])
