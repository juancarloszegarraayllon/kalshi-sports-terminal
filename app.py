import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date
from kalshi_python_sync import Configuration, KalshiClient

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
        font-size: 18px;
        font-weight: 700;
        color: #1e293b;
        margin: 15px 0;
        line-height: 1.2;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
        font-size: 13px;
        color: #64748b;
    }
    .footer-val {
        font-weight: 700;
        color: #1e293b;
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
st.sidebar.header("🎯 Filters")
search_query = st.sidebar.text_input("Search Teams", "")
# Default to today's date
selected_date = st.sidebar.date_input("Game Date", date.today())

# --- Fetch Events ---
@st.cache_data(ttl=300)
def fetch_sports_events():
    try:
        # Fetching parent events directly gives us clean game names
        response = client.get_events(limit=200, status="open")
        events_df = pd.DataFrame(response.to_dict().get("events", []))
        
        if events_df.empty:
            return pd.DataFrame()

        # Filter for sports based on prefixes
        sport_prefixes = ('NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'KXNBA', 'KXNFL')
        is_sport = (
            events_df['event_ticker'].str.startswith(sport_prefixes, na=False) |
            events_df['category'].str.contains('Sports', case=False, na=False)
        )
        return events_df[is_sport].copy()
    except Exception as e:
        st.error(f"Event Fetch Error: {e}")
        return pd.DataFrame()

events = fetch_sports_events()

if not events.empty:
    # --- Apply Date Filter ---
    # Convert strike_date to datetime objects for comparison
    events['strike_dt'] = pd.to_datetime(events['strike_date']).dt.date
    events = events[events['strike_dt'] == selected_date]

    # --- Apply Search Filter ---
    if search_query:
        events = events[events['title'].str.contains(search_query, case=False, na=False)]

    if events.empty:
        st.warning(f"No games found for {selected_date.strftime('%B %d, %Y')}.")
    else:
        st.write(f"Showing **{len(events)}** games for **{selected_date}**")
        
        # --- Grid Layout ---
        cols_per_row = 4
        for i in range(0, len(events), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(events):
                    event = events.iloc[i + j]
                    
                    # Clean title string
                    display_name = event['title'].replace('NBA: ', '').replace('Will the ', '').split('?')[0]

                    with grid_cols[j]:
                        st.markdown(f"""
                            <div class="market-card">
                                <div style="display: flex; justify-content: space-between;">
                                    <span class="badge-kalshi">KALSHI</span>
                                    <span style="color:#94a3b8; font-size:12px;">{event.get('category', 'Sports')}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px; margin-top: 15px;">
                                    <div style="font-size: 24px;">🏀</div>
                                    <div class="card-title">{display_name}</div>
                                </div>
                                <div class="card-footer">
                                    <div>Ticker: <span class="footer-val">{event['event_ticker']}</span></div>
                                    <div>Date: <span class="footer-val">{event['strike_dt']}</span></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
else:
    st.info("No active sports events found.")
