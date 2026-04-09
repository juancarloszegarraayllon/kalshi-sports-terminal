import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import requests

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# ----- CSS -----
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#6b7280!important;font-size:11px!important;text-transform:uppercase;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;color:#f0f0ff!important;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;position:relative;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#6b7280;text-transform:uppercase;}
.odds-price-yes{font-size:15px;font-weight:500;color:#4ade80;}
.odds-price-no{font-size:15px;font-weight:500;color:#f87171;}
.empty-state{text-align:center;padding:80px 20px;color:#374151;font-size:14px;}
</style>
""", unsafe_allow_html=True)

# ----- Constants -----
UTC = timezone.utc

TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),"Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),"Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),"Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),"Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),"Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),"Social":("👥","pill-default"),
    "World":("🌐","pill-default"),"Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

# ----- Fetch Kalshi data -----
def get_kalshi_data():
    url = "https://api.kalshi.com/v1/markets"  # Replace with actual endpoint & auth if needed
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        return pd.json_normalize(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# ----- Process df -----
def process_df(df):
    # Ensure necessary fields exist
    for col in ["title","category","start_time","yes_price","no_price"]:
        if col not in df.columns:
            df[col] = ""
    df["date"] = pd.to_datetime(df["start_time"]).dt.strftime("%Y-%m-%d %H:%M")
    return df

# ----- Display metrics -----
def display_metrics(df):
    total_markets = len(df)
    sports_markets = len(df[df['category']=='Sports'])
    elections_markets = len(df[df['category']=='Elections'])
    st.markdown(f"""
    <div class="metric-strip">
        <div class="metric-box"><div class="metric-label">Total Markets</div><div class="metric-value">{total_markets}</div></div>
        <div class="metric-box"><div class="metric-label">Sports</div><div class="metric-value">{sports_markets}</div></div>
        <div class="metric-box"><div class="metric-label">Elections</div><div class="metric-value">{elections_markets}</div></div>
    </div>
    """, unsafe_allow_html=True)

# ----- Display cards -----
def display_cards(df):
    if df.empty:
        st.markdown('<div class="empty-state">No markets available</div>', unsafe_allow_html=True)
        return

    st.markdown('<div class="card-grid">', unsafe_allow_html=True)
    for _, row in df.iterrows():
        icon, pill_class = CAT_META.get(row['category'], ("❓","pill-default"))
        st.markdown(f"""
        <div class="market-card">
            <div class="card-top">
                <div class="cat-pill {pill_class}">{icon} {row['category']}</div>
                <div class="date-text">{row['date']}</div>
            </div>
            <div class="card-title">{row['title']}</div>
            <div class="card-footer">
                <div class="odds-row">
                    <div class="odds-yes">
                        <div class="odds-label">Yes</div>
                        <div class="odds-price-yes">{row['yes_price']}</div>
                    </div>
                    <div class="odds-no">
                        <div class="odds-label">No</div>
                        <div class="odds-price-no">{row['no_price']}</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----- Main app -----
st.title("Kalshi Terminal 📡")

raw_df = get_kalshi_data()
df = process_df(raw_df)

# Sidebar filters
selected_cat = st.sidebar.selectbox("Category", ["All"] + TOP_CATS)
if selected_cat != "All":
    df = df[df['category']==selected_cat]

# Display metrics
display_metrics(df)

# Tabs per category
tab_names = ["All"] + TOP_CATS
tabs = st.tabs(tab_names)
for i, tab_name in enumerate(tab_names):
    with tabs[i]:
        if tab_name=="All":
            display_cards(df)
        else:
            display_cards(df[df['category']==tab_name])
