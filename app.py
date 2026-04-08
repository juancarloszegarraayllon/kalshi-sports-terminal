import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date

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
        height: 180px;
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
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
        font-size: 12px;
        color: #64748b;
        border-top: 1px solid #f1f5f9;
        padding-top: 10px;
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
    st.error(f"Init Error: {e}"); st.stop()

# --- Sidebar ---
st.sidebar.header("🎯 Filters")
selected_date = st.sidebar.date_input("Game Date", date.today())
search_query = st.sidebar.text_input("Search Teams", "")

@st.cache_data(ttl=300)
def fetch_sports_events():
    try:
        # Reduced limit to 100 to avoid 400 Bad Request
        # status="open" is standard, but we wrap it in a try-except
        response = client.get_events(limit=100, status="open")
        data = response.to_dict()
        events_list = data.get("events", [])
        
        if not events_list:
            return pd.DataFrame()

        events_df = pd.DataFrame(events_list)
        
        # Broad detection for any sports-related ticker or category
        sport_patterns = ['NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'PLAYER', 'KX']
        
        # Check title, event_ticker, and category for sport keywords
        is_sport = (
            events_df['event_ticker'].str.contains('|'.join(sport_patterns), na=False, case=False) |
            events_df['category'].str.contains('Sports', na=False, case=False) |
            events_df['title'].str.contains(' vs | beat | points | score ', na=False, case=False)
        )
        return events_df[is_sport].copy()
    except Exception as e:
        # If the API returns a 400, it might be the 'status' or 'limit' param
        st.error(f"API Fetch Error: {e}")
        return pd.DataFrame()

events = fetch_sports_events()

if not events.empty:
    # Standardize strike_date to match the date picker
    # Kalshi usually sends YYYY-MM-DD strings in the strike_date field
    events['strike_dt'] = pd.to_datetime(events['strike_date']).dt.date
    
    filtered_events = events[events['strike_dt'] == selected_date]

    if search_query:
        filtered_events = filtered_events[
            filtered_events['title'].str.contains(search_query, case=False, na=False)
        ]

    if filtered_events.empty:
        st.warning(f"No active sports events found for {selected_date}.")
        if not events.empty:
            st.info(f"Note: Found {len(events)} other sports events on different dates. Try changing the filter.")
    else:
        st.write(f"Showing **{len(filtered_events)}** games")
        
        # --- Grid Layout ---
        cols_per_row = 4
        for i in range(0, len(filtered_events), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(filtered_events):
                    ev = filtered_events.iloc[i + j]
                    
                    # Clean the title
                    title = ev['title'].replace('NBA: ', '').replace('Will the ', '').split('?')[0]

                    with grid_cols[j]:
                        st.markdown(f"""
                            <div class="market-card">
                                <div style="display: flex; justify-content: space-between;">
                                    <span class="badge-kalshi">KALSHI</span>
                                    <span style="color:#94a3b8; font-size:11px;">{ev.get('category', 'Sports')}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px; margin-top: 15px;">
                                    <div style="font-size: 22px;">🏀</div>
                                    <div class="card-title">{title}</div>
                                </div>
                                <div class="card-footer">
                                    <span>Ticker: <span class="footer-val">{ev['event_ticker']}</span></span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
else:
    st.info("Waiting for data from Kalshi...")
