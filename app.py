import streamlit as st
import pandas as pd
from time import sleep
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

st.set_page_config(page_title="Kalshi Sports Markets", layout="wide")
st.title("🏀 Kalshi Authenticated Sports Markets")

# Load secrets
api_key_id = st.secrets["KALSHI_API_KEY_ID"]
private_key_pem = st.secrets["KALSHI_PRIVATE_KEY_PEM"]

st.write("🔑 API Key loaded:", bool(api_key_id))
st.write("🔑 Private Key loaded:", bool(private_key_pem))

# Configure Kalshi client
config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key_pem
client = KalshiClient(config)

# Fetch markets
@st.cache_data(ttl=60)
def fetch_all_markets(status="open"):
    all_markets = []
    cursor = None

    while True:
        try:
            response = client.get_markets(limit=500, cursor=cursor, status=status)
        except ApiException as e:
            st.error(f"API Error: {e}")
            break

        markets_page = response.to_dict().get("markets", [])
        all_markets.extend(markets_page)

        cursor = response.to_dict().get("cursor")
        if not cursor:
            break

        sleep(0.1)  # avoid hitting rate limits

    return all_markets

# Load and filter markets
st.write("🔄 Fetching open markets from Kalshi...")
markets = fetch_all_markets()

if not markets:
    st.warning("No markets returned by authenticated API.")
else:
    df = pd.DataFrame(markets)

    # Only sports markets (if title contains common sports keywords)
    sports_keywords = ["NBA", "NFL", "MLB", "Soccer", "Football", "Basketball", "Tennis"]
    df_sports = df[df["title"].str.contains("|".join(sports_keywords), case=False, na=False)]

    if df_sports.empty:
        st.info("No sports markets found today.")
    else:
        # Convert prices to probabilities
        if "yes_ask" in df_sports.columns:
            df_sports["YES %"] = df_sports["yes_ask"] / 100
        if "no_ask" in df_sports.columns:
            df_sports["NO %"] = df_sports["no_ask"] / 100

        st.write(f"### Total sports markets: {len(df_sports)}")
        st.dataframe(df_sports[["title", "YES %", "NO %"]], use_container_width=True)
