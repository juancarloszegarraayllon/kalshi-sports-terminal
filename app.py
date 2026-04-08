import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timezone, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# Custom CSS for the "Card" look
st.markdown("""
    <style>
    .market-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e6e9ef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        min-height: 180px;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .badge-kalshi {
        background-color: #f0fdf4;
        color: #166534;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .mkts-count {
        color: #94a3b8;
        font-size: 11px;
    }
    .card-title {
        font-size: 15px;
        font-weight: 600;
        color: #1e293b;
        margin: 10px 0;
        height: 45px;
        overflow: hidden;
    }
    .card-footer {
        display: flex;
        gap: 15px;
        margin-top: 15px;
        font-size: 12px;
        color: #64748b;
    }
    .footer-val {
        font-weight: bold;
        color: #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏀 Kalshi Sports Terminal")

# --- API Setup (Retained from your code) ---
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

# --- Sidebar ---
st.sidebar.header("🎯 Market Filters")
search_query = st.sidebar.text_input("Search", "")

@st.cache_data(ttl=300)
def fetch_markets():
    try:
        response = client.get_markets(limit=1000, status="open")
        return pd.DataFrame(response.to_dict().get("markets", []))
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

df = fetch_markets()

if not df.empty:
    # --- Filtering Logic ---
    sport_prefixes = ('KX', 'NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN')
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df['event_ticker'].str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|score|points|win', case=False, na=False)
    )
    df_sports = df[is_sports].copy()

    if search_query:
        df_sports = df_sports[df_sports['title'].str.contains(search_query, case=False, na=False)]

    if not df_sports.empty:
        # Group markets by event_ticker to create one card per game
        # We aggregate to get the number of markets and total volume
        grouped = df_sports.groupby('event_ticker').agg({
            'title': 'first',
            'ticker': 'count',  # This represents 'mkts' count
            'volume': 'sum',
            'liquidity': 'sum'
        }).rename(columns={'ticker': 'mkts_count'}).reset_index()

        # Render as a Grid
        cols_per_row = 4
        for i in range(0, len(grouped), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(grouped):
                    row = grouped.iloc[i + j]
                    
                    # Clean up titles (remove specific bet details to show the game name)
                    display_title = row['title'].split('?')[0].replace('Will the ', '').strip()

                    with cols[j]:
                        st.markdown(f"""
                            <div class="market-card">
                                <div class="card-header">
                                    <div>
                                        <span class="badge-kalshi">KALSHI</span>
                                        <span style="color:#94a3b8; font-size:11px; margin-left:5px;">Sports</span>
                                    </div>
                                    <div class="mkts-count">{row['mkts_count']} mkts</div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <div style="background:#f1f5f9; padding:8px; border-radius:8px;">🏀</div>
                                    <div class="card-title">{display_title}</div>
                                </div>
                                <div class="card-footer">
                                    <div>Vol <span class="footer-val">${row['volume']/1000:,.1f}K</span></div>
                                    <div>Liq <span class="footer-val">${row['liquidity']/1000:,.1f}K</span></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
    else:
        st.warning("No sports markets found.")
else:
    st.info("No active markets found.")
