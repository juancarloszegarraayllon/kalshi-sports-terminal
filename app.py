import streamlit as st
import pandas as pd
from datetime import datetime, timezone

# Page config
st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:#6b7280!important;font-size:11px!important;letter-spacing:.08em;text-transform:uppercase;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;color:#f0f0ff!important;letter-spacing:-.02em;font-size:2.2rem!important;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;position:relative;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.cat-pill{font-size:10px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:4px;border:1px solid;white-space:nowrap;}
.date-text{font-size:11px;color:#6b7280;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1a;border-bottom:1px solid #1e1e32;gap:2px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#4b5563;border:none;font-size:12px;padding:8px 12px;}
.stTabs [aria-selected="true"]{background:#1e1e32!important;color:#a5b4fc!important;border-radius:6px 6px 0 0;}
</style>
""", unsafe_allow_html=True)

# Constants
UTC = timezone.utc

TOP_CATS = ["Sports","Elections","Politics","Economics","Financials",
            "Crypto","Companies","Entertainment","Climate and Weather",
            "Science and Technology","Health","Social","World","Transportation","Mentions"]

CAT_META = {
    "Sports":("🏟️","pill-sports"),
    "Elections":("🗳️","pill-elections"),
    "Politics":("🏛️","pill-politics"),
    "Economics":("📈","pill-economics"),
    "Financials":("💰","pill-financials"),
    "Crypto":("₿","pill-crypto"),
    "Companies":("🏢","pill-companies"),
    "Entertainment":("🎬","pill-entertainment"),
    "Climate and Weather":("🌍","pill-climate"),
    "Science and Technology":("🔬","pill-science"),
    "Health":("🏥","pill-health"),
    "Social":("👥","pill-default"),
    "World":("🌐","pill-default"),
    "Transportation":("✈️","pill-default"),
    "Mentions":("💬","pill-default"),
}

# Sidebar
st.sidebar.title("Kalshi Terminal")
selected_cat = st.sidebar.selectbox("Select Category", TOP_CATS)

# Placeholder for data fetching (replace with your API)
st.header(f"{CAT_META[selected_cat][0]} {selected_cat} Markets")
st.info("This is a placeholder table. Replace with live Kalshi data.")

# Dummy dataframe
data = pd.DataFrame({
    "Market": ["Market A", "Market B", "Market C"],
    "Yes Price": [0.55, 0.62, 0.48],
    "No Price": [0.45, 0.38, 0.52],
    "Category": [selected_cat]*3,
    "Updated": [datetime.now(UTC)]*3
})

# Display as a grid of cards
for idx, row in data.iterrows():
    st.markdown(f"""
    <div class="market-card">
        <div class="card-top">
            <span class="cat-pill {CAT_META[row['Category']][1]}">{row['Category']}</span>
            <span class="date-text">{row['Updated'].strftime('%Y-%m-%d %H:%M UTC')}</span>
        </div>
        <div class="card-title">{row['Market']}</div>
        <div class="odds-row">
            <div class="odds-yes">
                <div class="odds-label">Yes</div>
                <div class="odds-price-yes">{row['Yes Price']*100:.0f}%</div>
            </div>
            <div class="odds-no">
                <div class="odds-label">No</div>
                <div class="odds-price-no">{row['No Price']*100:.0f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
