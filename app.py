import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date
import time

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# Custom CSS for the clean "Card" look
st.markdown("""
    <style>
    .market-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #edf2f7;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        height: 200px;
        display: flex;
        flex-direction: column;
    }
    .badge-kalshi {
        background-color: #f0fdf4;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .card-title {
        font-size: 17px;
        font-weight: 700;
        color: #1e293b;
        margin: 15px 0;
        line-height: 1.2;
        flex-grow: 1;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #64748b;
        border-top: 1px solid #f1f5f9;
        padding-top: 10px;
        margin-top: auto;
    }
    .footer-val { font-weight: 700; color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

st.title("🏀 Kalshi Sports Terminal")

# --- API Setup ---
from kalshi_python_sync import Configuration, KalshiClient

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
st.sidebar.header("🎯 Filters")
selected_date = st.sidebar.date_input("Game Date", date.today())
search_query = st.sidebar.text_input("Search Teams / Events", "")
use_markets_api = st.sidebar.toggle("Use Markets API (more detailed)", value=True)
refresh_button = st.sidebar.button("🔄 Refresh Data Now")

@st.cache_data(ttl=120)
def fetch_data(use_markets=True):
    try:
        all_data = []
        cursor = None
        limit = 100 # Safe limit to avoid 400 errors
        
        with st.spinner(f"Fetching {'markets' if use_markets else 'events'}..."):
            for _ in range(3): # Fetch up to 300 items
                if use_markets:
                    response = client.get_markets(limit=limit, status="open", cursor=cursor)
                    key = "markets"
                else:
                    response = client.get_events(limit=limit, status="open", cursor=cursor)
                    key = "events"
                
                res_dict = response.to_dict()
                batch = res_dict.get(key, [])
                if not batch: break
                
                all_data.extend(batch)
                cursor = res_dict.get("cursor")
                if not cursor: break
                
        return pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"API Error: {e}")
        return pd.DataFrame()

if refresh_button:
    st.cache_data.clear()

df = fetch_data(use_markets_api)

if not df.empty:
    # 1. Broad Sports Detection
    sport_keywords = ['NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'KX', 'PLAYER', 'beat', 'vs']
    
    def is_sports_row(row):
        combined_text = f"{row.get('title', '')} {row.get('event_ticker', '')} {row.get('category', '')}".upper()
        return any(kw in combined_text for kw in sport_keywords)

    sports_df = df[df.apply(is_sports_row, axis=1)].copy()

    # 2. FIXED DATE PARSING
    if 'strike_date' in sports_df.columns:
        # Events API uses ISO strings
        sports_df['clean_date'] = pd.to_datetime(sports_df['strike_date']).dt.date
    elif 'close_time' in sports_df.columns:
        # Markets API uses Unix timestamps
        sports_df['clean_date'] = pd.to_datetime(sports_df['close_time'], unit='s').dt.date
    else:
        sports_df['clean_date'] = None

    # 3. Filtering
    filtered = sports_df[sports_df['clean_date'] == selected_date].copy()
    
    if search_query:
        filtered = filtered[filtered['title'].str.contains(search_query, case=False, na=False)]

    # Group by event_ticker so we don't show the same game 50 times
    if 'event_ticker' in filtered.columns:
        filtered = filtered.drop_duplicates(subset=['event_ticker'])

    # 4. UI Rendering
    if filtered.empty:
        st.warning(f"No sports found for {selected_date}.")
        with st.expander("🔍 Debug Raw Data"):
            st.write("First 5 items found (Any Category):")
            st.write(df[['title', 'event_ticker']].head())
            st.write("Total Sports Items in memory:", len(sports_df))
    else:
        st.success(f"Found {len(filtered)} matches", icon="🏆")
        cols = st.columns(3)
        for idx, (_, row) in enumerate(filtered.iterrows()):
            with cols[idx % 3]:
                title = str(row['title']).replace('Will the ', '').split('?')[0]
                st.markdown(f"""
                    <div class="market-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="badge-kalshi">KALSHI</span>
                            <span style="color:#94a3b8; font-size:11px;">{row.get('category', 'Sports')}</span>
                        </div>
                        <div class="card-title">{title}</div>
                        <div class="card-footer">
                            <span>{row['event_ticker']}</span>
                            <span class="footer-val">Active</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
else:
    st.info("No data received. Check your API Keys in Secrets.")
