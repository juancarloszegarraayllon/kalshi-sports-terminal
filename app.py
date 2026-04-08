import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, timezone, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# --- Custom CSS for Card UI ---
st.markdown("""
    <style>
    .market-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #edf2f7;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .market-card:hover {
        border-color: #cbd5e1;
        transform: translateY(-2px);
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .badge-kalshi {
        background-color: #f0fdf4;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .mkts-count {
        color: #94a3b8;
        font-size: 12px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #1e293b;
        margin: 10px 0;
        min-height: 48px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .card-footer {
        display: flex;
        gap: 20px;
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #f1f5f9;
        font-size: 12px;
        color: #64748b;
    }
    .footer-val {
        font-weight: 600;
        color: #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏀 Kalshi Sports Terminal")

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

# --- Sidebar Filters ---
st.sidebar.header("🎯 Market Filters")
search_query = st.sidebar.text_input("Search Teams or Sports", "")

# --- Fetch Markets ---
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
    # --- Filter Sports Markets ---
    sport_prefixes = ('KX', 'NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN')
    is_sports = (
        df['ticker'].str.startswith(sport_prefixes, na=False) |
        df.get('event_ticker', pd.Series()).str.startswith(sport_prefixes, na=False) |
        df['title'].str.contains('vs|score|points|win', case=False, na=False)
    )
    df_sports = df[is_sports].copy()

    if search_query:
        df_sports = df_sports[df_sports['title'].str.contains(search_query, case=False, na=False)]

    if not df_sports.empty:
        # --- Aggregation Logic (Prevents KeyError) ---
        cols = df_sports.columns
        
        # Determine available columns dynamically
        title_col = 'title' if 'title' in cols else 'ticker'
        vol_col = 'volume' if 'volume' in cols else ('open_interest' if 'open_interest' in cols else None)
        liq_col = 'liquidity' if 'liquidity' in cols else None
        
        agg_map = {title_col: 'first'}
        if vol_col: agg_map[vol_col] = 'sum'
        if liq_col: agg_map[liq_col] = 'sum'
        agg_map['ticker'] = 'count' # Count markets per game

        # Group by event_ticker if it exists, otherwise use title as a fallback
        group_by_col = 'event_ticker' if 'event_ticker' in cols else title_col
        grouped = df_sports.groupby(group_by_col).agg(agg_map).reset_index()

        # --- Display in Grid ---
        cols_per_row = 4
        for i in range(0, len(grouped), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(grouped):
                    row = grouped.iloc[i + j]
                    
                    # Data preparation
                    raw_title = str(row[title_col])
                    # Clean title: "Will the Pistons beat the 76ers?" -> "Pistons beat the 76ers"
                    clean_title = raw_title.split('?')[0].replace('Will the ', '').strip()
                    
                    vol_val = row.get(vol_col, 0) if vol_col else 0
                    liq_val = row.get(liq_col, 0) if liq_col else 0
                    mkts = row['ticker']

                    with grid_cols[j]:
                        st.markdown(f"""
                            <div class="market-card">
                                <div class="card-header">
                                    <div>
                                        <span class="badge-kalshi">KALSHI</span>
                                        <span style="color:#94a3b8; font-size:11px; margin-left:5px;">Sports</span>
                                    </div>
                                    <div class="mkts-count">{mkts} mkts</div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="font-size: 24px;">🏀</div>
                                    <div class="card-title">{clean_title}</div>
                                </div>
                                <div class="card-footer">
                                    <div>Vol <span class="footer-val">${vol_val/1000:,.1f}K</span></div>
                                    <div>Liq <span class="footer-val">${liq_val/1000:,.1f}K</span></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("No sports markets found for the current search.")
else:
    st.warning("No active markets found from Kalshi.")
