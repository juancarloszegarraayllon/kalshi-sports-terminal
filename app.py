import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalshi Sports Markets", layout="wide")
st.title("🏟️ Kalshi - Open Sports Markets")

# -----------------------------
# Kalshi API endpoint
# -----------------------------
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

# -----------------------------
# Fetch Data (cached)
# -----------------------------
@st.cache_data(ttl=60)
def get_markets():
    params = {
        "status": "open",
        "limit": 1000
    }
    headers = {
        "accept": "application/json"
    }
    try:
        response = requests.get(BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# -----------------------------
# Filter Sports Markets
# -----------------------------
def filter_sports_markets(data):
    if not data or "markets" not in data:
        return []

    results = []

    sports_keywords = [
        " vs ", " v ",
        "nba", "nfl", "mlb", "nhl",
        "soccer", "football", "tennis",
        "atp", "wta", "match", "game"
    ]

    for m in data["markets"]:
        title = m.get("title", "")
        subtitle = m.get("subtitle", "")
        category = m.get("category", "")

        text = f"{title} {subtitle}".lower()

        is_sports = any(k in text for k in sports_keywords)
        if category and "sport" in category.lower():
            is_sports = True

        if is_sports:
            results.append({
                "Game": title,
                "Ticker": m.get("ticker"),
                "YES Price": m.get("yes_ask"),
                "NO Price": m.get("no_ask"),
                "Volume": m.get("volume"),
                "Status": m.get("status")
            })

    return results

# -----------------------------
# Prepare DataFrame
# -----------------------------
def prepare_table(markets):
    if not markets:
        return pd.DataFrame()

    df = pd.DataFrame(markets)

    # Convert YES/NO to probabilities (0–1)
    if "YES Price" in df.columns:
        df["YES %"] = df["YES Price"] / 100
    if "NO Price" in df.columns:
        df["NO %"] = df["NO Price"] / 100

    # Sort by Volume descending
    if "Volume" in df.columns:
        df = df.sort_values(by="Volume", ascending=False)

    return df

# -----------------------------
# MAIN
# -----------------------------
data = get_markets()

if data:
    sports_markets = filter_sports_markets(data)
    df = prepare_table(sports_markets)

    st.write(f"### Total sports markets found: {len(df)}")

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No sports markets found.")
else:
    st.error("Failed to load data from Kalshi.")
