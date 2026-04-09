import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Setup ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="🏀")

# Custom CSS for that high-end Terminal look
st.markdown("""
    <style>
    .market-card {
        background-color: white; border-radius: 12px; padding: 20px;
        border: 1px solid #edf2f7; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px; height: 180px; display: flex; flex-direction: column;
    }
    .badge-kalshi {
        background-color: #f0fdf4; color: #166534; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 700;
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

# --- Deep Fetch Logic (Pagination) ---
@st.cache_data(ttl=120)
def fetch_all_sport_events():
    all_events = []
    cursor = None
    
    # We fetch up to 3 pages (600 events) to make sure we find all sports
    with st.spinner("Deep-scanning Kalshi feed..."):
        for _ in range(3):
            try:
                response = client.get_events(limit=200, status="open", cursor=cursor)
                data = response.to_dict()
                batch = data.get("events", [])
                if not batch: break
                
                all_events.extend(batch)
                cursor = data.get("cursor")
                if not cursor: break
            except:
                break
                
    if not all_events: return pd.DataFrame()
    
    df = pd.DataFrame(all_events)
    
    # Specific Sport Identifiers
    sport_keywords = ['NBA', 'MLB', 'NHL', 'NFL', 'SOC', 'TEN', 'KX', 'PLAYER']
    is_sport = (
        df['event_ticker'].str.contains('|'.join(sport_keywords), na=False, case=False) |
        df['category'].str.contains('Sports', na=False, case=False) |
        df['title'].str.contains(' vs | beat | at ', na=False, case=False)
    )
    return df[is_sport].copy()

df_sports = fetch_all_sport_events()

if not df_sports.empty:
    # Sidebar Filters
    st.sidebar.header("Filter Results")
    search = st.sidebar.text_input("Quick Find (Team/League)")
    show_all = st.sidebar.toggle("Show all upcoming days", value=True)
    
    # Date processing
    df_sports['game_date'] = pd.to_datetime(df_sports['strike_date']).dt.date
    
    filtered = df_sports
    if not show_all:
        filtered = filtered[filtered['game_date'] == date.today()]
    if search:
        filtered = filtered[filtered['title'].str.contains(search, case=False, na=False)]

    # Display results
    st.write(f"Found **{len(filtered)}** Sport Events")
    
    cols = st.columns(4)
    for idx, (_, row) in enumerate(filtered.iterrows()):
        with cols[idx % 4]:
            # Formatting the title
            display_title = row['title'].split(':')[-1].replace('Will the ', '').split('?')[0].strip()
            
            st.markdown(f"""
                <div class="market-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="badge-kalshi">KALSHI</span>
                        <span style="color:#94a3b8; font-size:11px;">{row['game_date']}</span>
                    </div>
                    <div class="card-title">{display_title}</div>
                    <div class="card-footer">
                        <span>{row['event_ticker']}</span>
                        <span class="footer-val">{row.get('category', 'Sports')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("No active sports found. Note: Kalshi resets many sports tickers at midnight UTC.")
