import streamlit as st
import pandas as pd
import tempfile
import re
from datetime import datetime, date
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# --- Custom CSS (Updated for Date Badges) ---
st.markdown("""
    <style>
    .market-card {
        background-color: white; border-radius: 12px; padding: 20px;
        border: 1px solid #edf2f7; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px; height: 190px; display: flex; flex-direction: column;
    }
    .badge-container {
        display: flex; justify-content: space-between; align-items: center;
    }
    .badge-kalshi {
        background-color: #f0fdf4; color: #166534; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 700;
    }
    .badge-date {
        background-color: #f1f5f9; color: #475569; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 600;
    }
    .card-title {
        font-size: 17px; font-weight: 700; color: #1e293b;
        margin: 15px 0; line-height: 1.2; flex-grow: 1;
    }
    .card-footer {
        display: flex; justify-content: space-between; margin-top: auto;
        font-size: 12px; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 10px;
    }
    .footer-val { font-weight: 700; color: #1e293b; }
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
    st.error(f"Connect Error: {e}"); st.stop()

# --- Helper: Extract Date from Ticker ---
def get_display_date(row):
    # Try to find date in ticker (e.g., KXNBA-26APR08)
    ticker = str(row.get('event_ticker', ''))
    match = re.search(r'(\d{2})([A-Z]{3})(\d{2})', ticker)
    if match:
        return f"{match.group(2)} {match.group(3)}, 20{match.group(1)}"
    
    # Fallback to strike_date
    try:
        dt = pd.to_datetime(row['strike_date'])
        return dt.strftime("%b %d, %Y")
    except:
        return "Upcoming"

# --- Fetch Data ---
@st.cache_data(ttl=120)
def fetch_sports():
    all_events = []
    cursor = None
    for _ in range(3): # Paginate through 600 items
        try:
            response = client.get_events(limit=200, status="open", cursor=cursor)
            data = response.to_dict()
            batch = data.get("events", [])
            if not batch: break
            all_events.extend(batch)
            cursor = data.get("cursor")
            if not cursor: break
        except: break
    
    if not all_events: return pd.DataFrame()
    df = pd.DataFrame(all_events)
    
    # Keyword filter for sports
    sport_keys = ['NBA', 'MLB', 'NHL', 'NFL', 'SOC', 'TEN', 'KX', 'PLAYER']
    mask = (df['event_ticker'].str.contains('|'.join(sport_keys), na=False, case=False) |
            df['category'].str.contains('Sports', na=False, case=False))
    return df[mask].copy()

df_sports = fetch_sports()

if not df_sports.empty:
    search = st.sidebar.text_input("Search Teams")
    
    filtered = df_sports
    if search:
        filtered = filtered[filtered['title'].str.contains(search, case=False, na=False)]

    st.write(f"Showing **{len(filtered)}** Sport Events")
    
    cols = st.columns(4)
    for idx, (_, row) in enumerate(filtered.iterrows()):
        with cols[idx % 4]:
            # Clean Title
            title = row['title'].split(':')[-1].replace('Will the ', '').split('?')[0].strip()
            # Get Formatted Date
            event_date = get_display_date(row)
            
            st.markdown(f"""
                <div class="market-card">
                    <div class="badge-container">
                        <span class="badge-kalshi">KALSHI</span>
                        <span class="badge-date">{event_date}</span>
                    </div>
                    <div class="card-title">{title}</div>
                    <div class="card-footer">
                        <span>Ticker: <span class="footer-val">{row['event_ticker']}</span></span>
                        <span>{row.get('category', 'Sports')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("No active sports found. Try refreshing in a few minutes.")
