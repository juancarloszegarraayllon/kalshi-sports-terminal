import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalshi Terminal", layout="wide", page_icon="📡")

# === Categories & Subcategories ===
CATEGORIES = {
    "Sports": ["Football","Basketball","Tennis","Other Sports"],
    "Elections": ["US","International"],
    "Politics": ["US","International"],
    "Economics": ["Macro","Commodities","Currencies"],
    "Financials": ["Stocks","Indices","Options"],
    "Crypto": ["Bitcoin","Ethereum","Altcoins"],
    "Companies": ["Tech","Finance","Retail"],
    "Entertainment": ["Movies","Music","TV Shows"],
    "Climate and Weather": ["Weather Events","Climate Change"],
    "Science and Technology": ["Space","Innovation","AI"],
    "Health": ["Pharma","Diseases","Wellness"],
    "Social": ["Trends","Memes","Discussions"],
    "World": ["Geopolitics","Conflicts","Global Events"],
    "Transportation": ["Aviation","Automotive","Shipping"],
    "Mentions": ["Media","Social Media"]
}

# === Example Kalshi Data Structure ===
# Replace this with live API fetching
raw_events = [
    {
        "title": "EPL: Arsenal vs Man U",
        "category": "Sports",
        "subcategory": "Football",
        "series_ticker": "KXEPL",
        "markets": [
            {"yes_bid":0.45,"no_bid":0.55},
            {"yes_bid":0.40,"no_bid":0.60}
        ]
    },
    {
        "title": "US Elections 2024",
        "category": "Elections",
        "subcategory": "US",
        "series_ticker": "KXELEC",
        "markets": [
            {"yes_bid":0.6,"no_bid":0.4}
        ]
    },
    {
        "title": "BTC Price Above $30k",
        "category": "Crypto",
        "subcategory": "Bitcoin",
        "series_ticker": "KXBTC",
        "markets": [
            {"yes_bid":0.7,"no_bid":0.3}
        ]
    },
]

# === Process Events ===
def flatten_events(events):
    rows = []
    for e in events:
        for m in e.get("markets", []):
            rows.append({
                "title": e.get("title",""),
                "category": e.get("category","Other"),
                "subcategory": e.get("subcategory","Other"),
                "series_ticker": e.get("series_ticker",""),
                "yes": m.get("yes_bid","—"),
                "no": m.get("no_bid","—")
            })
    return pd.DataFrame(rows)

df = flatten_events(raw_events)

# === Streamlit UI ===
st.title("📡 Kalshi Terminal")

# Sidebar Category Filter
selected_category = st.sidebar.selectbox("Category", ["All"] + list(CATEGORIES.keys()))
subcats = CATEGORIES.get(selected_category, []) if selected_category != "All" else []
selected_subcat = st.sidebar.selectbox("Subcategory", ["All"] + subcats) if subcats else "All"

# Filter DataFrame
filtered_df = df.copy()
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]
if selected_subcat != "All":
    filtered_df = filtered_df[filtered_df["subcategory"] == selected_subcat]

# Display Events
if filtered_df.empty:
    st.info("No events found for this selection.")
else:
    for _, row in filtered_df.iterrows():
        st.markdown(f"""
        **{row['title']}**  
        *Category:* {row['category']} | *Subcategory:* {row['subcategory']}  
        **Series Ticker:** {row['series_ticker']}  
        ✅ Yes: {row['yes']} | ❌ No: {row['no']}
        """)
        st.markdown("---")
