import streamlit as st
import pandas as pd
import tempfile
import re
from datetime import datetime, date
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# Clean, Dark-themed CSS to match a "Sportsbook" look
st.markdown("""
    <style>
    .market-card {
        background-color: #ffffff; border-radius: 10px; padding: 18px;
        border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 20px; height: 170px; display: flex; flex-direction: column;
    }
    .badge-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
    .sport-tag {
        background-color: #eff6ff; color: #1e40af; padding: 3px 8px;
        border-radius: 4px; font-size: 10px; font-weight: 800; text-transform: uppercase;
    }
    .date-tag { color: #64748b; font-size: 11px; font-weight: 500; }
    .card-title {
        font-size: 16px; font-weight: 700; color: #0f172a;
        margin-top: 5px; line-height: 1.4; flex-grow: 1;
    }
    .ticker-footer {
        font-family: monospace; font-size: 10px; color: #94a3b8;
        border-top: 1px solid #f1f5f9; padding-top: 8px; margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏟️ Kalshi Live Sports")

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
    st.error("API connection failed. Check your Streamlit Secrets."); st.stop()

# --- Targeted Sports Fetch ---
@st.cache_data(ttl=60)
def fetch_real_sports():
    # Targeted Series Tickers for 2026 Sports
    target_series = ['KXNBAGAME', 'KXMLBGAME', 'KXNHLGAME', 'KXNFLGAME', 'KXMASTERS', 'KXTENNIS']
    all_sports = []
    
    try:
        # We query the events endpoint for each major sport series directly
        for series in target_series:
            response = client.get_events(limit=50, status="open", series_ticker=series)
            data = response.to_dict()
            events = data.get("events", [])
            all_sports.extend(events)
        
        if not all_sports:
            # Fallback: Broad category search if specific series aren't populated
            response = client.get_events(limit=100, status="open")
            all_sports = [e for e in response.to_dict().get("events", []) 
                          if 'sport' in e.get('category', '').lower()]

        return pd.DataFrame(all_sports)
    except Exception as e:
        st.error(f"Error fetching sports data: {e}")
        return pd.DataFrame()

df = fetch_real_sports()

if not df.empty:
    # Sidebar Search
    search = st.sidebar.text_input("Filter by Team (e.g. Lakers)")
    if search:
        df = df[df['title'].str.contains(search, case=False, na=False)]

    # Clean duplicates and sort by date
    df = df.drop_duplicates(subset=['event_ticker'])
    
    st.write(f"Active Matchups: **{len(df)}**")
    
    cols = st.columns(4)
    for i, (_, row) in enumerate(df.iterrows()):
        with cols[i % 4]:
            # Formatting Title (Lakers at Celtics etc)
            display_title = row['title'].split(':')[-1].replace('Will the ', '').split('?')[0].strip()
            
            # Format Date
            raw_date = pd.to_datetime(row['strike_date'])
            display_date = raw_date.strftime("%b %d")

            # Determine Icon
            ticker = row['event_ticker']
            icon = "🏀" if "NBA" in ticker else "⚾" if "MLB" in ticker else "🏒" if "NHL" in ticker else "🏆"

            st.markdown(f"""
                <div class="market-card">
                    <div class="badge-row">
                        <span class="sport-tag">{row.get('category', 'PRO SPORT')}</span>
                        <span class="date-tag">{display_date}</span>
                    </div>
                    <div class="card-title">{icon} {display_title}</div>
                    <div class="ticker-footer">
                        ID: {row['event_ticker']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.warning("No live sports found in the API series. This usually happens between game sets or if the API is currently filtering the 'open' status differently.")
