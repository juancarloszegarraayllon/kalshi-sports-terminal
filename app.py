import streamlit as st
import pandas as pd
import tempfile
from datetime import datetime, date, timedelta
from kalshi_python_sync import Configuration, KalshiClient

# --- Page Config ---
st.set_page_config(page_title="Kalshi Sports", layout="wide", page_icon="🏀")

# --- Custom CSS for the Kalshi Website Look ---
st.markdown("""
    <style>
    .market-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #edf2f7;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        height: 190px;
        transition: transform 0.2s;
    }
    .market-card:hover { border-color: #cbd5e1; transform: translateY(-2px); }
    .badge-kalshi {
        background-color: #f0fdf4; color: #166534; padding: 4px 10px;
        border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase;
    }
    .card-title {
        font-size: 17px; font-weight: 700; color: #1e293b; margin: 15px 0; line-height: 1.3;
    }
    .card-footer {
        display: flex; justify-content: space-between; font-size: 12px;
        color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 12px; margin-top: 10px;
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

# --- Data Fetching ---
@st.cache_data(ttl=300)
def get_kalshi_events():
    try:
        # Fetching 'events' gives the top-level game names
        response = client.get_events(limit=200, status="open")
        df = pd.DataFrame(response.to_dict().get("events", []))
        
        # Filter for Sports
        sport_tags = ['NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'KX']
        is_sport = df['event_ticker'].str.contains('|'.join(sport_tags), na=False) | \
                   df['category'].str.contains('Sports', case=False, na=False)
        return df[is_sport].copy()
    except:
        return pd.DataFrame()

df = get_kalshi_events()

if not df.empty:
    # --- Date Logic ---
    # Standardize Kalshi's UTC strike_date to a date object
    df['game_date'] = pd.to_datetime(df['strike_date']).dt.date
    
    # Sidebar Filter
    st.sidebar.header("Navigation")
    view_option = st.sidebar.radio("View Games for:", ["Today & Tomorrow", "Specific Date", "All Upcoming"])
    
    if view_option == "Today & Tomorrow":
        target_dates = [date.today(), date.today() + timedelta(days=1)]
        filtered = df[df['game_date'].isin(target_dates)]
    elif view_option == "Specific Date":
        user_date = st.sidebar.date_input("Select Date", date.today())
        filtered = df[df['game_date'] == user_date]
    else:
        filtered = df

    # Search Bar
    search = st.sidebar.text_input("Search Team/Player")
    if search:
        filtered = filtered[filtered['title'].str.contains(search, case=False, na=False)]

    # --- Render Cards ---
    if filtered.empty:
        st.warning("No games found for this selection.")
    else:
        st.write(f"Showing **{len(filtered)}** Events")
        cols = st.columns(4)
        for idx, (_, row) in enumerate(filtered.iterrows()):
            with cols[idx % 4]:
                # Clean title: Removes "Will the" and "?" 
                clean_title = row['title'].replace('Will the ', '').split('?')[0]
                
                st.markdown(f"""
                    <div class="market-card">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="badge-kalshi">KALSHI</span>
                            <span style="color:#94a3b8; font-size:11px;">{row['game_date']}</span>
                        </div>
                        <div class="card-title">{clean_title}</div>
                        <div class="card-footer">
                            <span>Ticker <span class="footer-val">{row['event_ticker']}</span></span>
                            <span>{row.get('category', 'Sports')}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
else:
    st.info("No active sports events found.")
