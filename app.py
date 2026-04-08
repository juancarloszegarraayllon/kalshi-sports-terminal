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
    now = int(datetime.utcnow().timestamp())
    # Looking 2 weeks ahead to ensure we catch all sports seasons
    future = now + (14 * 24 * 60 * 60)

    try:
        response = client.get_markets(
            limit=500, # Increased limit to find more sports
            status="open",
            min_close_ts=now,
            max_close_ts=future
        )
        data = response.to_dict().get("markets", [])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_all_markets()

if not df.empty:
    # 1. Broadened Keywords for April Sports (NBA Playoffs/MLB start)
    sports_list = [
        "NBA", "NFL", "MLB", "NHL", "Soccer", "Tennis", "UFC", "Golf", 
        "Lakers", "Warriors", "Yankees", "Mets", "Inter Miami", "Champions League"
    ]
    
    # 2. Filtering Logic
    is_sports = df["title"].str.contains("|".join(sports_list), case=False, na=False)
    if "category" in df.columns:
        is_sports = is_sports | (df["category"].str.contains("Sports", case=False, na=False))

    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # 3. Safe Column Processing (Prevents the KeyError)
    for target_df in [df_sports, df_other]:
        if not target_df.empty:
            # Use 'yes_ask' or 'last_price' for probability
            price_col = "yes_ask" if "yes_ask" in target_df.columns else "last_price"
            if price_col in target_df.columns:
                target_df["Prob %"] = target_df[price_col].apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "N/A")
            else:
                target_df["Prob %"] = "N/A"
            
            # Ensure close_time is readable
            if "close_time" in target_df.columns:
                target_df["Ends"] = pd.to_datetime(target_df["close_time"]).dt.strftime('%b %d, %H:%M')
            else:
                target_df["Ends"] = "Unknown"

    # --- UI Tabs ---
    tab1, tab2 = st.tabs(["🏆 Sports Markets", "📈 All Other Markets"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports matches matched your current filters. Check 'All Other Markets'.")
        else:
            # Only display columns we know exist now
            st.dataframe(df_sports[["title", "Prob %", "Ends"]], use_container_width=True, hide_index=True)

    with tab2:
        if df_other.empty:
            st.info("No non-sports markets found.")
        else:
            st.dataframe(df_other[["title", "Prob %", "Ends"]], use_container_width=True, hide_index=True)

else:
    st.info("No markets found in the given timeframe.")
