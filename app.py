import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient
from kalshi_python_sync.rest import ApiException

st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide")
st.title("🏀 Kalshi Sports Terminal")

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
def fetch_markets():
    now = int(datetime.utcnow().timestamp())
    future = now + (7 * 24 * 60 * 60) 

    try:
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
    # 1. EXCLUSION LIST: Words that definitely mean it's NOT sports
    not_sports_keywords = ["inflation", "recession", "fed", "rate", "cpi", "election", "biden", "trump", "court"]
    
    # 2. INCLUSION LIST: Reliable sports prefixes and keywords
    sport_prefixes = ('NBA', 'MLB', 'NHL', 'NFL', 'SOC', 'TEN', 'UFC', 'KX')
    sport_keywords = ["vs", "score", "points", "win", "total", "spread"]

    # --- THE FILTER LOGIC ---
    # First, identify everything that is potentially a sport
    is_sports_potential = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains("|".join(sport_keywords), case=False, na=False)
    )
    
    # Second, identify everything that is definitely NOT a sport
    is_not_sports = df['title'].str.contains("|".join(not_sports_keywords), case=False, na=False)
    
    # Final Sports Filter: Must be potential sport AND must NOT be on the exclusion list
    df_sports = df[is_sports_potential & ~is_not_sports].copy()
    df_other = df[~is_sports_potential | is_not_sports].copy()

    # 3. Data Processing
    for frame in [df_sports, df_other]:
        if not frame.empty:
            # Handle new _dollars fields or fallback to cents
            col = "yes_ask_dollars" if "yes_ask_dollars" in frame.columns else "yes_ask"
            if col in frame.columns:
                frame["Price"] = frame[col].apply(lambda x: f"${float(x):.2f}" if col.endswith("dollars") else f"{int(x)}¢")
            
            if 'close_time' in frame.columns:
                frame["Ends (UTC)"] = pd.to_datetime(frame["close_time"]).dt.strftime('%m/%d %H:%M')

    # --- UI ---
    tab1, tab2 = st.tabs(["🏆 Sports Only", "📈 Economics & General"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports events found.")
        else:
            cols = [c for c in ["title", "Price", "Ends (UTC)"] if c in df_sports.columns]
            st.dataframe(df_sports[cols].sort_values("Ends (UTC)"), use_container_width=True, hide_index=True)

    with tab2:
        cols = [c for c in ["title", "Price", "Ends (UTC)"] if c in df_other.columns]
        st.dataframe(df_other[cols], use_container_width=True, hide_index=True)
