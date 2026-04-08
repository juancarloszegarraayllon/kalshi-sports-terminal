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
@st.cache_data(ttl=300)
def fetch_kalshi_data(tickers):
    try:
        # 1. Setup Configuration
        config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
        config.api_key_id = KEY_ID
        config.private_key_pem = PRIVATE_KEY
        
        # 2. Initialize Client
        client = KalshiClient(config)
        
        all_data = []
        for ticker in tickers:
            # Fetching markets for the specific sport ticker (NBA, NFL, etc.)
            response = client.get_markets(series_ticker=ticker, status="open")
            
            # Extract markets from the response object
            markets = response.markets if hasattr(response, 'markets') else []
            
            for m in markets:
                all_data.append({
                    "Event": m.title,
                    "Yes Price ($)": m.yes_ask / 100,
                    "No Price ($)": m.no_ask / 100,
                    "Volume": m.volume,
                    "Ticker": m.ticker
                })
        
        return pd.DataFrame(all_data)
    except Exception as e:
        return str(e)

# --- UI Layout ---
st.sidebar.header("Filters")
selected_sports = st.sidebar.multiselect("Sports to Track", ["NBA", "NFL", "MLB"], default=["NBA", "NFL"])

if st.sidebar.button("Refresh Feed"):
    st.cache_data.clear()

data_result = fetch_kalshi_data(selected_sports)

if isinstance(data_result, pd.DataFrame):
    if not data_result.empty:
        # Display Stats
        c1, c2 = st.columns(2)
        c1.metric("Total Markets", len(data_result))
        c2.metric("Highest Volume", data_result.iloc[data_result['Volume'].idxmax()]['Event'])

        # Display Table
        st.subheader("Live Market Odds")
        st.dataframe(data_result, use_container_width=True)

        # Chart
        st.subheader("Sentiment Analysis (Probability of 'Yes')")
        fig = px.bar(data_result, x='Event', y='Yes Price ($)', color='Volume', range_y=[0,1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No active games found. Markets might be closed for the day.")
else:
    st.error(f"Critical Error: {data_result}")
