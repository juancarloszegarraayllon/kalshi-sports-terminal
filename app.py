import streamlit as st
import pandas as pd
import tempfile
import time
from datetime import datetime, date, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# --- Custom CSS for the Screenshot Look ---
st.markdown("""
    <style>
    .market-card {
        background-color: white; border-radius: 12px; padding: 18px;
        border: 1px solid #edf2f7; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px; height: 160px; display: flex; flex-direction: column;
    }
    .badge-row { display: flex; justify-content: space-between; margin-bottom: 12px; }
    .sport-badge {
        background-color: #f0fdf4; color: #166534; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase;
    }
    .date-badge { color: #64748b; font-size: 11px; font-weight: 600; }
    .card-title {
        font-size: 17px; font-weight: 700; color: #1e293b;
        margin: 5px 0; line-height: 1.3; flex-grow: 1;
    }
    .ticker-footer {
        font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9;
        padding-top: 8px; margin-top: auto;
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
    st.error("API connection failed."); st.stop()

# --- Single-Call Fetch (Avoids 429) ---
@st.cache_data(ttl=300)
def fetch_sports_unified():
    try:
        # Fetch one big batch (200 events) to stay under rate limits
        response = client.get_events(limit=200, status="open")
        all_events = response.to_dict().get("events", [])
        if not all_events: return pd.DataFrame()
        
        df = pd.DataFrame(all_events)
        
        # Only keep rows that look like sports
        sport_keys = ['NBA', 'MLB', 'NHL', 'NFL', 'SOC', 'TEN', 'GOLF', 'KX']
        is_sport = (
            df['event_ticker'].str.contains('|'.join(sport_keys), na=False, case=False) |
            df['category'].str.contains('Sports', na=False, case=False)
        )
        return df[is_sport].copy()
    except Exception as e:
        if "429" in str(e):
            st.error("Rate limit hit. Waiting 10 seconds...")
            time.sleep(10)
        return pd.DataFrame()

df = fetch_sports_unified()

if not df.empty:
    # --- Sidebar Filters ---
    st.sidebar.header("Navigation")
    search = st.sidebar.text_input("Search Team")
    # Buffer date for UTC: show Today and Tomorrow by default
    date_buffer = [date.today(), date.today() + timedelta(days=1)]
    
    # Process Dates
    df['clean_date'] = pd.to_datetime(df['strike_date']).dt.date
    
    # Filtering
    filtered = df[df['clean_date'].isin(date_buffer)]
    if search:
        filtered = filtered[filtered['title'].str.contains(search, case=False, na=False)]
    
    # Remove duplicates for the same game
    filtered = filtered.drop_duplicates(subset=['event_ticker'])

    if filtered.empty:
        st.warning("No games found for today/tomorrow. Check 'Show All' in sidebar.")
        if st.sidebar.checkbox("Show All Upcoming Games"):
            filtered = df
    
    # --- Render Grid ---
    if not filtered.empty:
        st.write(f"Showing **{len(filtered)}** Sport Events")
        cols = st.columns(4)
        for i, (_, row) in enumerate(filtered.iterrows()):
            with cols[i % 4]:
                # Title Cleanup
                title = row['title'].split(':')[-1].replace('Will the ', '').split('?')[0].strip()
                
                # Dynamic Icon
                ticker = row['event_ticker'].upper()
                icon = "🏀" if "NBA" in ticker else "⚾" if "MLB" in ticker else "🏒" if "NHL" in ticker else "🏟️"
                
                # Format Date Badge
                display_date = row['clean_date'].strftime("%b %d")

                st.markdown(f"""
                    <div class="market-card">
                        <div class="badge-row">
                            <span class="sport-badge">KALSHI</span>
                            <span class="date-badge">{display_date}</span>
                        </div>
                        <div class="card-title">{icon} {title}</div>
                        <div class="ticker-footer">
                            {row['event_ticker']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
else:
    st.info("No active sports data found. The API might be resetting for the day.")
