import streamlit as st
import pandas as pd
from datetime import datetime, timezone

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# ----- CSS styling -----
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Mono',monospace;}
.stApp{background:#0a0a0f;}
section[data-testid="stSidebar"]{background:#0f0f1a!important;border-right:1px solid #1e1e32;}
h1{font-family:'Syne',sans-serif!important;color:#f0f0ff;}
.metric-strip{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
.metric-box{background:#0f0f1a;border:1px solid #1e1e32;border-radius:10px;padding:14px 20px;flex:1;min-width:120px;}
.metric-label{font-size:10px;color:#4b5563;text-transform:uppercase;margin-bottom:4px;}
.metric-value{font-size:22px;font-weight:500;color:#a5b4fc;}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;}
.market-card{background:#0f0f1a;border:1px solid #1e1e32;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s;}
.market-card:hover{border-color:#4f46e5;transform:translateY(-2px);}
.cat-pill{font-size:10px;font-weight:500;padding:3px 10px;border-radius:4px;border:1px solid;white-space:nowrap;}
.pill-sports{background:#1a2e1a;color:#4ade80;border-color:#166534;}
.pill-elections{background:#2e1a1e;color:#f472b6;border-color:#9d174d;}
.pill-politics{background:#1e1a2e;color:#818cf8;border-color:#3730a3;}
.pill-financials{background:#2e2a1a;color:#fb923c;border-color:#9a3412;}
.date-text{font-size:11px;color:#6b7280;}
.card-title{font-size:14px;font-weight:500;color:#e2e8f0;margin-bottom:12px;}
.odds-row{display:flex;gap:8px;}
.odds-yes{flex:1;background:#0d2d1a;border:1px solid #166534;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-no{flex:1;background:#2d0d0d;border:1px solid #7f1d1d;border-radius:6px;padding:5px 8px;text-align:center;}
.odds-label{font-size:9px;color:#6b7280;text-transform:uppercase;}
.odds-price-yes{font-size:15px;font-weight:500;color:#4ade80;}
.odds-price-no{font-size:15px;font-weight:500;color:#f87171;}
.stTabs [data-baseweb="tab-list"]{background:#0f0f1a;border-bottom:1px solid #1e1e32;gap:2px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#4b5563;border:none;font-size:12px;padding:8px 12px;}
.stTabs [aria-selected="true"]{background:#1e1e32!important;color:#a5b4fc!important;border-radius:6px 6px 0 0;}
</style>
""", unsafe_allow_html=True)

# ----- Placeholder Kalshi data -----
def get_kalshi_data():
    data = [
        {"title": "Galatasaray vs Goztepe Winner", "category": "Sports", "start_time": "2026-04-08T18:00:00Z", "yes_price": 0.65, "no_price": 0.35},
        {"title": "2026 US Presidential Election - Winner", "category": "Elections", "start_time": "2026-11-03T12:00:00Z", "yes_price": 0.52, "no_price": 0.48},
        {"title": "Tesla Stock Up Tomorrow?", "category": "Financials", "start_time": "2026-04-09T14:30:00Z", "yes_price": 0.70, "no_price": 0.30},
        {"title": "SpaceX Starship Launch Success", "category": "Science and Technology", "start_time": "2026-04-10T09:00:00Z", "yes_price": 0.85, "no_price": 0.15},
        {"title": "Oscars Best Picture 2026", "category": "Entertainment", "start_time": "2026-03-27T20:00:00Z", "yes_price": 0.40, "no_price": 0.60},
    ]
    return pd.DataFrame(data)

df = get_kalshi_data()
df['start_time'] = pd.to_datetime(df['start_time'])

# ----- Metrics strip -----
total_markets = len(df)
avg_yes = df['yes_price'].mean()
avg_no = df['no_price'].mean()

st.markdown("<h1>Kalshi Terminal</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div class="metric-strip">
    <div class="metric-box"><div class="metric-label">Total Markets</div><div class="metric-value">{total_markets}</div></div>
    <div class="metric-box"><div class="metric-label">Avg Yes Price</div><div class="metric-value">{avg_yes:.2f}</div></div>
    <div class="metric-box"><div class="metric-label">Avg No Price</div><div class="metric-value">{avg_no:.2f}</div></div>
</div>
""", unsafe_allow_html=True)

# ----- Tabs for categories -----
categories = sorted(df['category'].unique())
tab_selection = st.tabs(categories)

for i, cat in enumerate(categories):
    with tab_selection[i]:
        cat_df = df[df['category'] == cat]
        if cat_df.empty:
            st.write("No markets in this category.")
        else:
            st.markdown('<div class="card-grid">', unsafe_allow_html=True)
            for _, row in cat_df.iterrows():
                pill_class = "pill-" + row['category'].lower().replace(" ", "")
                date_str = row['start_time'].strftime("%Y-%m-%d %H:%M UTC")
                st.markdown(f"""
                <div class="market-card">
                    <div class="cat-pill {pill_class}">{row['category']}</div>
                    <div class="card-title">{row['title']}</div>
                    <div class="odds-row">
                        <div class="odds-yes">
                            <div class="odds-label">Yes</div>
                            <div class="odds-price-yes">{row['yes_price']:.2f}</div>
                        </div>
                        <div class="odds-no">
                            <div class="odds-label">No</div>
                            <div class="odds-price-no">{row['no_price']:.2f}</div>
                        </div>
                    </div>
                    <div class="date-text">{date_str}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
