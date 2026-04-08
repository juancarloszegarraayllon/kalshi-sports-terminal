import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timedelta
from kalshi_python_sync import Configuration, KalshiClient

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="🏀")
st.title("🏀 Kalshi Sports & Markets")

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

@st.cache_data(ttl=60)
def fetch_everything():
    now = int(datetime.utcnow().timestamp())
    # Looking 3 days ahead to catch today's and tomorrow's slates
    future = now + (3 * 24 * 60 * 60)
    try:
        response = client.get_markets(limit=1000, status="open", min_close_ts=now, max_close_ts=future)
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_everything()

if not df.empty:
    # 1. Expanded Sports Detection
    # Catching League codes, vs matchups, and common player stats keywords
    sport_indicators = [
        "NBA", "MLB", "NHL", "NFL", "UFC", "SOC", "UCL", "KX",
        " vs ", " vs. ", " @ ", " win ", " score ", " points ", " total "
    ]
    
    # Identify Sports
    is_sports = (
        df['title'].str.contains("|".join(sport_indicators), case=False, na=False) |
        df['ticker'].str.contains("NBA|MLB|NHL|SOC|UFC", case=False, na=False)
    )
    
    # 2. Hard Exclusion for Macro/Economics (pushing Inflation away from Sports)
    is_macro = df['title'].str.contains("inflation|cpi|rate|fed|gdp|election", case=False, na=False)
    
    df_sports = df[is_sports & ~is_macro].copy()
    df_other = df[~is_sports | is_macro].copy()

    # 3. Defensive Processing
    for frame in [df_sports, df_other]:
        if not frame.empty:
            # Handle the new 2026 dollar fields
            price_col = "yes_ask_dollars" if "yes_ask_dollars" in frame.columns else "yes_ask"
            if price_col in frame.columns:
                frame["Prob %"] = frame[price_col].apply(lambda x: f"{int(float(x)*100)}%" if price_col.endswith("dollars") else f"{int(x)}%")
            else:
                frame["Prob %"] = "N/A"
            
            frame["Ends (UTC)"] = pd.to_datetime(frame["close_time"]).dt.strftime('%m/%d %H:%M')

    # --- UI Layout ---
    tab1, tab2 = st.tabs(["🏆 Sports Board", "📈 Other Markets"])

    with tab1:
        if df_sports.empty:
            st.warning("No sports matches matched the current filters. They may be in 'Other Markets'.")
        else:
            st.write(f"Showing **{len(df_sports)}** live sports events.")
            # Selecting only existing columns to prevent errors
            display_cols = [c for c in ["title", "Prob %", "Ends (UTC)", "ticker"] if c in df_sports.columns]
            st.dataframe(df_sports[display_cols].sort_values("Ends (UTC)"), use_container_width=True, hide_index=True)

    with tab2:
        if not df_other.empty:
            st.dataframe(df_other[["title", "Prob %", "Ends (UTC)"]], use_container_width=True, hide_index=True)

else:
    st.info("No active markets found. Checking the exchange...")
