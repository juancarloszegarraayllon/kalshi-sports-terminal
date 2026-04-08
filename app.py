import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

# --- Streamlit setup ---
st.set_page_config(page_title="Kalshi Sports Markets", layout="wide")
st.title("🏀 Kalshi Sports Markets Dashboard")

# --- Load secrets ---
api_key_id = st.secrets["KALSHI_API_KEY_ID"]
private_key_path = st.secrets["KALSHI_PRIVATE_KEY_PATH"]

st.write(f"🔑 API Key loaded: {bool(api_key_id)}")
st.write(f"🔑 Private Key path loaded: {bool(private_key_path)}")

# --- Initialize Kalshi client ---
try:
    config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
    config.api_key_id = api_key_id
    config.private_key_pem_path = private_key_path
    client = KalshiClient(config)
    st.success("✅ Kalshi client initialized successfully!")
except Exception as e:
    st.error(f"Error initializing Kalshi client: {e}")
    st.stop()

# --- Fetch today's sports markets safely ---
@st.cache_data(ttl=300)
def fetch_sports_markets_today():
    all_markets = []
    cursor = None
    max_retries = 3

    # UTC datetime for today
    today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_utc = today_utc + timedelta(days=1)

    while True:
        retries = 0
        while retries < max_retries:
            try:
                response = client.get_markets(
                    limit=500,
                    cursor=cursor,
                    status="open",
                    start_time_min=today_utc,
                    start_time_max=tomorrow_utc
                )
                break
            except ApiException as e:
                if e.status == 429:
                    retries += 1
                    wait_time = 2 * retries
                    st.warning(f"Rate limit hit. Waiting {wait_time}s before retrying...")
                    time.sleep(wait_time)
                else:
                    st.error(f"API Error: {e}")
                    return pd.DataFrame()

        markets_page = response.to_dict().get("markets", [])
        if not markets_page:
            break  # exit if no markets returned
        all_markets.extend(markets_page)

        cursor = response.to_dict().get("cursor")
        if not cursor:
            break

        time.sleep(0.5)  # small delay to avoid rate limit

    # Filter sports markets
    df = pd.DataFrame(all_markets)
    if df.empty:
        return pd.DataFrame()

    sports_keywords = ["NBA", "NFL", "MLB", "Soccer", "Football", "Basketball", "Tennis"]
    df_sports = df[df["title"].str.contains("|".join(sports_keywords), case=False, na=False)]
    return df_sports

# --- Load and display ---
st.write("🔄 Fetching today's sports markets from Kalshi...")
df_sports = fetch_sports_markets_today()

if df_sports.empty:
    st.info("No sports markets found today.")
else:
    # Add probabilities if available
    if "yes_ask" in df_sports.columns:
        df_sports["YES %"] = df_sports["yes_ask"] / 100
    if "no_ask" in df_sports.columns:
        df_sports["NO %"] = df_sports["no_ask"] / 100

    columns_to_show = ["title", "start_time", "YES %", "NO %"]
    columns_to_show = [c for c in columns_to_show if c in df_sports.columns]

    st.write(f"### Total sports markets today: {len(df_sports)}")
    st.dataframe(df_sports[columns_to_show].sort_values("start_time"), use_container_width=True)
