import streamlit as st
import pandas as pd
from kalshi_python_sync import Configuration, KalshiClient
import plotly.express as px

# --- Dashboard Config ---
st.set_page_config(page_title="Kalshi Sports Terminal", layout="wide", page_icon="📈")

st.title("🏆 Kalshi Daily Sports Extraction")

# --- API Configuration ---
# Hardcoded credentials as requested
KEY_ID = "8c40b181-5fda-4515-a554-8f73c224b1f7"
PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAs2IGcClv1Wzfeo96M0Fp+TQz+RPg4uH4WOD7nAi+o3hU0sMn
TSnDU9Aq1ZS8+wHS+Tdmgtu4C6TogtDSX0PBnrHtJAS4Mo786nx7XREApJ2XjL2/
2tQUyctwhj6GTnJ2suCWYhC/APLUc9ZfVpFYg49tkAandVhJXXHG4IcxGnYg2GtP
Saf8X4IzawtH2ZOd9KGbZBvzt6dxerwqAbVGLsVIx8G95GUOJqpM35UCVy5bMiSf
szwf9uezBcXnq2WhBMPabm+dLkQjIbiDJrvcdCescZVkZFMDI3qBUpJszZFw/4+N
R1+S9pZISNUV6bcZ2aaNKoEj3AuBIlqCZ/Z/OQIDAQABAoIBACo/tqt5HvViAJqh
q1LiH78JfAo4k9lsBm2Mg8ZCyv++ah//xcRnRzF40HXgY8gsrE91LGg6rrTTYM3a
uAmm8DXbyzIWCHoj8k6aBgYr6H5c/aIw2LyGAeVrTHPZyxEz5WAJBHJRZmMnTkGA
JpFBh1rpD5GB97PsGM9w6jncrYSBFASYjq3LiLj8A8yioYL+qMNOlKNneMxwzawf
g53c386SgrJIgNjiZDfQOc23574iK6gUpeYPYGwYBaTYEz2N+k1QdDF1KUqJCvhJ
GyM8C+dr9AXbJtn+9vaeNeURP94opQaLBHtGepTapJeDKdYpYoXOnzMd0VJOY7ns
qT18FzcCgYEAznAud8Bqr2nK4dgOdnXdL7O2MHCV2C/IuWjiGyLf72q/W1Z2OtLg
2Sr8K+P30fAEDxpdLvXupGa0te67otVBnSmW5i6UZKpC+01vaF7Pe5bzRWDTEBVH
nv3YYlU98gas11W2A1VXF4wr70jL6eErD1vJthVOAJEQkm3ur5pEFv8CgYEA3nMC
KtzAG3xszADS56Lqb/qgRXo1wef0T54iVyipiwSiNHJtgEaTnwRQTgMwobQpxz3g
3aJShlxWnizpi4UtOwFVclTH6Vn7Ar1J/CJeDPf5uavCzo4v67AO7XyRny7OlrVN
FC+hilyWhej+rRXWG3BAjMkj1s72FstNYPGuYccCgYEAvGYA4mUGeCPSdh4ZxN54
B+q4oKh++BdT1nHzt9QyDmubS54ytChz732dOekI591lturWk9759auNzGOddlOt
V+L2xgdIgj4odvQKcnPkYuQ2C+D7fjgNbvo3mjY1HEYfQz4DqDMgEmtoRS5oen92
LsQT6Eq1Lys0to4BQN1Gur0CgYEAuEHRYMmbgujsgYqJJ/+Fax3RVdtl3ekRMEXP
MhznWtSKuyCxXRiYvJXpIsV3qem+1V+G/G6xJsQjpz+Sb9PvZDm1mk9pi/vRdDJw
rx2Ug+9/dfE1Gr0iKnqZ0tNlF9LAoosofnj5uM76i480LRCyWeYAQd12Bz9FDhp2
TL/D7w8CgYEAtydtilvLJv55/JSMmCnLqMlpJLx5gWNqJr/Gh7kq59B6d+HcGWnI
NT5wDD/gTnB1kCLLY9cnZI9AXCJrWs6fMxqm9CgUpoAYg7lqCDKqTHva87nvCF0P
m6V/krn3WsZeW2JHZq7X+R4CyDNCVoCVf6QXLwnbyiGyW78vBz8iKeY=
-----END RSA PRIVATE KEY-----"""

# --- Data Extraction Logic ---
@st.cache_data(ttl=60)
def fetch_kalshi_data(search_query):
    try:
        # 1. Setup Configuration
        config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
        config.api_key_id = KEY_ID
        config.private_key_pem = PRIVATE_KEY
        
        # 2. Initialize Client
        client = KalshiClient(config)
        
        # 3. Use 'get_markets' with a broad limit to find active games
        # We filter for 'open' markets to see live trading data
        response = client.get_markets(limit=200, status="open")
        markets = response.markets if hasattr(response, 'markets') else []
        
        all_data = []
        for m in markets:
            # Check if the market title contains our search word (e.g. "NBA")
            if search_query.upper() in m.title.upper() or search_query.upper() in m.ticker.upper():
                all_data.append({
                    "Event": m.title,
                    "Yes Price ($)": m.yes_ask / 100 if hasattr(m, 'yes_ask') else 0,
                    "No Price ($)": m.no_ask / 100 if hasattr(m, 'no_ask') else 0,
                    "Volume": m.volume if hasattr(m, 'volume') else 0,
                    "Ticker": m.ticker,
                    "Close Time": m.close_time
                })
        
        return pd.DataFrame(all_data)
    except Exception as e:
        return str(e)

# --- UI Layout ---
st.sidebar.header("Search Markets")
query = st.sidebar.text_input("Enter Sport (e.g., NBA, MLB, NHL)", value="NBA")

if st.sidebar.button("Refresh Feed"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.write("Current Status: **Connected**")

data_result = fetch_kalshi_data(query)

if isinstance(data_result, pd.DataFrame):
    if not data_result.empty:
        # Metrics Row
        c1, c2, c3 = st.columns(3)
        c1.metric("Active Markets", len(data_result))
        c2.metric("Top Vol Market", data_result.iloc[data_result['Volume'].idxmax()]['Ticker'])
        c3.metric("Avg. Price", f"${data_result['Yes Price ($)'].mean():.2f}")

        # Live Data Table
        st.subheader(f"Live {query} Market Odds")
        st.dataframe(data_result.sort_values(by="Volume", ascending=False), use_container_width=True)

        # Visualization
        st.subheader("Price Distribution")
        fig = px.bar(data_result, x='Ticker', y='Yes Price ($)', color='Volume', 
                     hover_data=['Event'], range_y=[0, 1])
        st.plotly_chart(fig, use_container_width=True)
        
        # CSV Export
        csv = data_result.to_csv(index=False).encode('utf-8')
        st.download_button("Download as CSV", csv, "kalshi_export.csv", "text/csv")
    else:
        st.warning(f"No active '{query}' markets found. Try searching for 'MLB' or
