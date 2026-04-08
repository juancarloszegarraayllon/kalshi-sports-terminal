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
        font-size: 17px;
        font-weight: 700;
        color: #1e293b;
        margin: 15px 0;
        line-height: 1.2;
        min-height: 40px;
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

# --- API Setup (Retained) ---
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

# --- Sidebar Filters ---
st.sidebar.header("🎯 Filters")
selected_date = st.sidebar.date_input("Game Date", date.today())
search_query = st.sidebar.text_input("Search Teams", "")

@st.cache_data(ttl=300)
def fetch_sports_events():
    try:
        # Increase limit to 500 to catch all daily sports
        response = client.get_events(limit=500, status="open")
        events_df = pd.DataFrame(response.to_dict().get("events", []))
        if events_df.empty: return pd.DataFrame()

        # Broad sport detection
        sport_keywords = ['NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'PLAYER', 'KX']
        is_sport = (
            events_df['event_ticker'].str.contains('|'.join(sport_keywords), na=False) |
            events_df['category'].str.contains('Sports', case=False, na=False) |
            events_df['title'].str.contains(' vs | beat ', case=False, na=False)
        )
        return events_df[is_sport].copy()
    except Exception as e:
        st.error(f"API Error: {e}"); return pd.DataFrame()

events = fetch_sports_events()

if not events.empty:
    # 1. Standardize Date Filtering (Handles UTC ISO strings)
    events['strike_dt'] = pd.to_datetime(events['strike_date']).dt.tz_convert(None).dt.date
    filtered_events = events[events['strike_dt'] == selected_date]

    # 2. Search Filter
    if search_query:
        filtered_events = filtered_events[
            filtered_events['title'].str.contains(search_query, case=False, na=False) |
            filtered_events['sub_title'].str.contains(search_query, case=False, na=False)
        ]

    if filtered_events.empty:
        st.warning(f"No games found for {selected_date}. Try checking the day before or after due to timezone shifts.")
    else:
        st.write(f"Showing **{len(filtered_events)}** games")
        cols_per_row = 4
        for i in range(0, len(filtered_events), cols_per_row):
            grid_cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(filtered_events):
                    ev = filtered_events.iloc[i + j]
                    
                    # Formatting Title: Use Title, fallback to Subtitle
                    title = ev['title'] if ev['title'] else ev.get('sub_title', 'Unknown Game')
                    title = title.replace('NBA: ', '').replace('Will the ', '').split('?')[0]

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
                                    <span>ID: <span class="footer-val">{ev['event_ticker']}</span></span>
                                    <span>Date: <span class="footer-val">{ev['strike_dt']}</span></span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
else:
    st.info("No active sports events found in Kalshi's feed.")
