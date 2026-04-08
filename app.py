import streamlit as st
import pandas as pd
from pykalshi import KalshiClient, MarketStatus
import plotly.express as px

# --- Dashboard Config ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="📈")

st.title("🏆 Kalshi Daily Sports Extraction")
st.markdown("Extracting live market data for NBA, NFL, and MLB games.")

# --- Sidebar Configuration ---
st.sidebar.header("Data Settings")
# Note: For public sports data, pykalshi often doesn't even need a login.
# We'll initialize it simply.
st.sidebar.info("Connected to Kalshi Public API")

st.sidebar.divider()
sport_filter = st.sidebar.multiselect("Select Sports", ["NBA", "NFL", "MLB", "NHL"], default=["NBA", "NFL"])

# --- Data Extraction Logic ---
@st.cache_data(ttl=300) 
def fetch_kalshi_data(tickers):
    try:
        # Initialize client without arguments for public data
        client = KalshiClient() 
        
        all_markets = []
        for ticker in tickers:
            # Using the correct Enum-based status from the library
            markets = client.get_markets(series_ticker=ticker, status=MarketStatus.OPEN)
            all_markets.extend(markets)
        
        if not all_markets:
            return pd.DataFrame()

        # Build Dataframe using the library's built-in conversion if available
        # or manual mapping for reliability:
        data = []
        for m in all_markets:
            data.append({
                "Event": m.title,
                "Yes Price": m.yes_ask_dollars if hasattr(m, 'yes_ask_dollars') else (m.yes_ask / 100),
                "No Price": m.no_ask_dollars if hasattr(m, 'no_ask_dollars') else (m.no_ask / 100),
                "Volume": m.volume if hasattr(m, 'volume') else 0,
                "Ticker": m.ticker
            })
        return pd.DataFrame(data)
    except Exception as e:
        return str(e)

# --- Main Dashboard Display ---
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()

df = fetch_kalshi_data(sport_filter)

if isinstance(df, pd.DataFrame) and not df.empty:
    # Top Level Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Markets", len(df))
    
    # Check if Volume exists before calculating max
    if df['Volume'].sum() > 0:
        m2.metric("Most Active", df.iloc[df['Volume'].idxmax()]['Event'])
    else:
        m2.metric("Most Active", "N/A")
        
    avg_price = df['Yes Price'].mean()
    m3.metric("Avg. Yes Price", f"${avg_price:.2f}")

    # Data Table
    st.subheader("Active Game Markets")
    st.dataframe(df, use_container_width=True)

    # Visualization
    st.subheader("Market Sentiment (Probability of 'Yes')")
    fig = px.bar(df, x='Event', y='Yes Price', 
                 labels={'Yes Price': 'Price ($)'},
                 color_continuous_scale='Viridis',
                 range_y=[0, 1])
    st.plotly_chart(fig, use_container_width=True)

    # Export Feature
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Game Data as CSV", data=csv, file_name="kalshi_sports_data.csv", mime="text/csv")

elif isinstance(df, str):
    st.error(f"Technical Error: {df}")
    st.info("This can happen if the Kalshi API is undergoing maintenance.")
else:
    st.warning("No active games found for the selected tickers. Try selecting different sports in the sidebar.")
