import streamlit as st
import pandas as pd
from datetime import timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# === STYLES ===
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
.pill-sports{background:#1a2e1a;color:#4ade80;border-color:#166534;}
.pill-elections{background:#2e1a1e;color:#f472b6;border-color:#9d174d;}
.pill-politics{background:#1e1a2e;color:#818cf8;border-color:#3730a3;}
.pill-economics{background:#2e2a1a;color:#fbbf24;border-color:#92400e;}
.pill-financials{background:#2e2a1a;color:#fb923c;border-color:#9a3412;}
.pill-crypto{background:#1e2a2e;color:#67e8f9;border-color:#0e7490;}
.pill-companies{background:#2e1e2e;color:#d8b4fe;border-color:#7e22ce;}
.pill-entertainment{background:#2e1e1a;color:#fdba74;border-color:#c2410c;}
.pill-climate{background:#1a2e2e;color:#22d3ee;border-color:#164e63;}
.pill-science{background:#1e2e1a;color:#86efac;border-color:#14532d;}
.pill-health{background:#2e1a2e;color:#e879f9;border-color:#701a75;}
.pill-default{background:#1e1e32;color:#94a3b8;border-color:#2d2d55;}
.date-text{font-size:11px;color:#6b7280;}
.card-icon{font-size:20px;margin-bottom:6px;display:block;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;line-height:1.45;margin-bottom:12px;min-height:58px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.card-footer{border-top:1px solid #1a1a2e;padding-top:10px;}
.ticker-text{font-size:10px;color:#374151;letter-spacing:.06em;display:block;margin-bottom:8px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;}
.odds-price-yes{font-size:15px;font-weight:500;color:#4ade80;}
.odds-price-no{font-size:15px;font-weight:500;color:#f87171;}
.empty-state{text-align:center;padding:80px 20px;color:#374151;font-size:14px;}
hr{border-color:#1e1e32!important;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1a;border-bottom:1px solid #1e1e32;gap:2px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#4b5563;border:none;font-size:12px;padding:8px 12px;}
.stTabs [aria-selected="true"]{background:#1e1e32!important;color:#a5b4fc!important;border-radius:6px 6px 0 0;}
</style>
""", unsafe_allow_html=True)

UTC = timezone.utc

# === CATEGORIES & SUBCATEGORIES ===
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

CAT_TAGS = {
    "Elections":["US Elections","International elections","House","Primaries"],
    "Politics":["Trump","Congress","International","SCOTUS & courts","Local","Iran"],
    "Economics":["Fed","Inflation","GDP","Jobs & Economy","Housing","Oil and energy","Global Central Banks"],
    "Financials":["S&P","Nasdaq","Metals","Agriculture","Oil & Gas","Treasuries","EUR/USD","USD/JPY"],
    "Crypto":["BTC","ETH","SOL","DOGE","XRP","BNB","HYPE"],
    "Companies":["IPOs","Elon Musk","CEOs","Product launches","Layoffs"],
    "Entertainment":["Music","Television","Movies","Awards","Video games","Oscars"],
    "Climate and Weather":["Hurricanes","Daily temperature","Snow and rain","Climate change","Natural disasters"],
    "Science and Technology":["AI","Space","Medicine","Energy"],
    "Health":["Diseases"],
    "Mentions":["Earnings","Politicians","Sports"],
}

# === HELPER FUNCTIONS ===
def detect_sport(series_ticker):
    # Minimal demo
    soccer_series = ["KXEPL","KXUCL","KXUEL"]
    if str(series_ticker).upper() in soccer_series:
        return "Soccer"
    return ""

def get_soccer_comp(series_ticker):
    mapping = {"KXEPL":"EPL","KXUCL":"Champions League","KXUEL":"Europa League"}
    return mapping.get(series_ticker.upper(), "")

def fmt_pct(val):
    try:
        return f"{float(val)*100:.0f}%"
    except:
        return "—"

def process_df(df):
    if isinstance(df, pd.DataFrame):
        df = df.copy()
    elif isinstance(df, dict) and "events" in df:
        df = df["events"]
    if not isinstance(df, list):
        df = []
    if not df:
        return pd.DataFrame()
    
    df = pd.json_normalize(df)
    df["title"] = df.get("title","").astype(str)
    df["category"] = df.get("category","Other").astype(str)
    df["series_ticker"] = df.get("series_ticker","").astype(str)
    
    df["_sport"] = df["series_ticker"].apply(detect_sport)
    df["_is_sport"] = df["_sport"] != ""
    
    df["_soccer_comp"] = df.apply(
        lambda r: get_soccer_comp(r["series_ticker"]) if r["_sport"]=="Soccer" else "",
        axis=1
    )
    
    # Dummy odds
    df["_yes"] = "—"
    df["_no"] = "—"
    
    return df

# === STREAMLIT UI ===
st.title("📡 Kalshi Terminal")

# Placeholder: raw_df comes from Kalshi API
# raw_df = client.get_events()  
# Demo dummy data:
raw_df = [
    {"title":"EPL: Arsenal vs Man U","category":"Sports","series_ticker":"KXEPL","markets":[{"yes_bid":0.45,"no_bid":0.55}]},
    {"title":"US Elections 2024","category":"Elections","series_ticker":"KXELEC","markets":[{"yes_bid":0.6,"no_bid":0.4}]},
]

df = process_df(raw_df)

if df.empty:
    st.markdown('<div class="empty-state">No events found.</div>', unsafe_allow_html=True)
else:
    for _, row in df.iterrows():
        icon, pill_class = CAT_META.get(row["category"],("❓","pill-default"))
        st.markdown(f"""
        <div class="market-card">
            <div class="card-top">
                <span class="cat-pill {pill_class}">{icon} {row['category']}</span>
                <span class="date-text">—</span>
            </div>
            <div class="card-title">{row['title']}</div>
            <div class="odds-row">
                <div class="odds-yes">
                    <div class="odds-label">Yes</div>
                    <div class="odds-price-yes">{row['_yes']}</div>
                </div>
                <div class="odds-no">
                    <div class="odds-label">No</div>
                    <div class="odds-price-no">{row['_no']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
