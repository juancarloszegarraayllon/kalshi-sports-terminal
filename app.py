import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta, date
from kalshi_python_sync import Configuration, KalshiClient

st.set_page_config(page_title="Kalshi Game Day", layout="wide", page_icon="🏀")
st.title("🏟️ Today's Sports Board")

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

# --- Sidebar Controls ---
st.sidebar.header("🕹️ Game Controls")
view_mode = st.sidebar.radio("Market Status", ["Active (Betting Open)", "Closed (Games In-Progress/Done)"])
status_filter = "open" if view_mode == "Active (Betting Open)" else "closed"

# Time range for TODAY
today_start = datetime.combine(date.today(), datetime.min.time())
today_start_ts = int(today_start.timestamp())
three_days_out_ts = today_start_ts + (3 * 24 * 60 * 60)

@st.cache_data(ttl=60)
def fetch_today_slates(status):
    try:
        response = client.get_markets(
            limit=1000, 
            status=status,
            min_close_ts=today_start_ts,
            max_close_ts=three_days_out_ts
        )
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

df = fetch_today_slates(status_filter)

if not df.empty:
    # 2026 Sport Detection (KX Prefixes are standard for NBA/MLB now)
    sport_prefixes = ('KX', 'NBA', 'MLB', 'NHL', 'SOC', 'UCL', 'TEN')
    
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|@|score|win', case=False, na=False)
    )
    # Filter out the Argentina Inflation / Macro stuff
    is_macro = df['title'].str.contains("inflation|cpi|rate|fed", case=False, na=False)
    
    df_today = df[is_sports & ~is_macro].copy()

    if not df_today.empty:
        # Probability / Price Logic
        col = "yes_ask_dollars" if "yes_ask_dollars" in df_today.columns else "yes_ask"
        if col in df_today.columns:
            df_today["Price"] = df_today[col].apply(lambda x: f"{int(float(x)*100)}%" if col.endswith("dollars") else f"{int(x)}%")
        
        df_today["Time (UTC)"] = pd.to_datetime(df_today["close_time"]).dt.strftime('%H:%M')

        # Display
        st.write(f"### {view_mode} - April 8, 2026")
        
        # Group by League for better reading
        for league in ["NBA", "MLB", "SOC"]:
            league_df = df_today[df_today['ticker'].str.contains(league, na=False)]
            if not league_df.empty:
                st.subheader(f"{league} Slate")
                st.dataframe(
                    league_df[["title", "Price", "Time (UTC)"]].sort_values("Time (UTC)"),
                    use_container_width=True, hide_index=True
                )
        
        # Show everything else sports-related
        other_sports = df_today[~df_today['ticker'].str.contains("NBA|MLB|SOC", na=False)]
        if not other_sports.empty:
            st.subheader("Other Sports")
            st.dataframe(other_sports[["title", "Price", "Time (UTC)"]], use_container_width=True, hide_index=True)
    else:
        st.warning(f"No {status_filter} sports markets found for today.")
else:
    st.info("Gathering market data...")
