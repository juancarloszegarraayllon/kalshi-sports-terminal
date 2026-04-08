import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date
import time

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# Custom CSS
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
    st.success("✅ Connected to Kalshi", icon="🔗")
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
def fetch_all_events():
    try:
        all_events = []
        cursor = None
        with st.spinner("Fetching events from Kalshi..."):
            while True:
                response = client.get_events(
                    limit=200,
                    status="open",
                    cursor=cursor
                )
                data = response.to_dict()
                events_list = data.get("events", [])
                
                if not events_list:
                    break
                    
                all_events.extend(events_list)
                cursor = data.get("cursor")
                
                if not cursor:
                    break
                time.sleep(0.1)  # Be gentle on the API
        
        return pd.DataFrame(all_events) if all_events else pd.DataFrame()
    
    except Exception as e:
        st.error(f"Events API Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_all_markets():
    try:
        all_markets = []
        cursor = None
        with st.spinner("Fetching markets from Kalshi..."):
            while True:
                response = client.get_markets(
                    limit=200,
                    status="open",
                    cursor=cursor
                )
                data = response.to_dict()
                markets_list = data.get("markets", [])
                
                if not markets_list:
                    break
                    
                all_markets.extend(markets_list)
                cursor = data.get("cursor")
                
                if not cursor:
                    break
                time.sleep(0.1)
        
        return pd.DataFrame(all_markets) if all_markets else pd.DataFrame()
    
    except Exception as e:
        st.error(f"Markets API Error: {e}")
        return pd.DataFrame()

# Fetch data
if refresh_button:
    st.cache_data.clear()

if use_markets_api:
    df = fetch_all_markets()
    ticker_col = 'ticker'
    title_col = 'title'
    category_col = 'category'
    event_ticker_col = 'event_ticker'
else:
    df = fetch_all_events()
    ticker_col = 'event_ticker'
    title_col = 'title'
    category_col = 'category'
    event_ticker_col = 'event_ticker'

# Sports filtering
if not df.empty:
    sport_keywords = ['NBA', 'MLB', 'NFL', 'NHL', 'soccer', 'tennis', 'basketball', 
                     'baseball', 'football', 'hockey', 'KXNBA', 'KXMLB', 'KXNFL', 
                     'KXNH', 'game', 'spread', 'total', 'props', 'player']
    
    def is_sports(row):
        text = ' '.join(str(x).lower() for x in row if isinstance(x, str))
        return any(kw.lower() in text for kw in sport_keywords)
    
    sports_df = df[df.apply(is_sports, axis=1)].copy()
    
    # Date handling
    if 'close_time' in sports_df.columns:
        sports_df['strike_dt'] = pd.to_datetime(sports_df['close_time'], errors='coerce').dt.date
    elif 'strike_date' in sports_df.columns:
        sports_df['strike_dt'] = pd.to_datetime(sports_df['strike_date'], errors='coerce').dt.date
    else:
        sports_df['strike_dt'] = date.today()
    
    # Filter by date and search
    filtered = sports_df[sports_df['strike_dt'] == selected_date].copy()
    
    if search_query:
        mask = (
            filtered[title_col].str.contains(search_query, case=False, na=False) |
            filtered[event_ticker_col].str.contains(search_query, case=False, na=False)
        )
        filtered = filtered[mask]
    
    filtered = filtered.drop_duplicates(subset=[event_ticker_col])
    
    if filtered.empty:
        st.warning(f"No sports events found for **{selected_date}** with current filters.")
        st.info(f"Total sports items found overall: {len(sports_df)}")
    else:
        st.success(f"Showing **{len(filtered)}** sports events for {selected_date}", icon="🏟️")
        
        # Display as cards
        cols_per_row = 3
        for i in range(0, len(filtered), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(filtered):
                    ev = filtered.iloc[i + j]
                    title = str(ev.get(title_col, 'No Title')).replace('Will ', '').replace('?', '').strip()
                    
                    with grid_cols[j]:
                        st.markdown(f"""
                            <div class="market-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span class="badge-kalshi">KALSHI</span>
                                    <span style="color:#94a3b8; font-size:11px;">{ev.get(category_col, 'Sports')}</span>
                                </div>
                                <div class="card-title">{title}</div>
                                <div class="card-footer">
                                    <span>Ticker: <span class="footer-val">{ev.get(event_ticker_col, 'N/A')}</span></span>
                                    <span>Markets: <span class="footer-val">{len(filtered) if use_markets_api else 'Event'}</span></span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
else:
    st.info("No data received from Kalshi yet...")

st.caption("Data refreshes every 2 minutes • Powered by Kalshi API")
