import requests
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Kalshi Sports Markets", layout="wide")

st.title("🏟️ Kalshi - Today's Sports Markets")

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
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


# -----------------------------
# Identify Sports Markets
# -----------------------------
def is_sports_market(title):
    if not title:
        return False

    keywords = [
        " vs ", " v ", "game", "match",
        "nba", "mlb", "nfl", "soccer",
        "tennis", "atp", "wta"
    ]

    title_lower = title.lower()
    return any(k in title_lower for k in keywords)


# -----------------------------
# Filter Today's Markets
# -----------------------------
def filter_today_markets(data):
    if not data or "markets" not in data:
        return []

    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)

    results = []

    for m in data["markets"]:
        title = m.get("title")
        close_time = m.get("close_time")

        if not title or not close_time:
            continue

        # Convert close_time safely
        try:
            dt = datetime.fromisoformat(close_time.replace("Z", ""))
        except:
            continue

        # Filter: next 24h + sports only
        if now <= dt <= tomorrow and is_sports_market(title):
            results.append({
                "Game": title,
                "Ticker": m.get("ticker"),
                "YES Price": m.get("yes_ask"),
                "NO Price": m.get("no_ask"),
                "Close Time (UTC)": dt.strftime("%Y-%m-%d %H:%M")
            })

    return results


# -----------------------------
# Convert to DataFrame
# -----------------------------
def prepare_table(markets):
    import pandas as pd

    if not markets:
        return pd.DataFrame()

    df = pd.DataFrame(markets)

    # Convert prices to probabilities
    if "YES Price" in df.columns:
        df["YES %"] = df["YES Price"] / 100

    if "NO Price" in df.columns:
        df["NO %"] = df["NO Price"] / 100

    return df.sort_values(by="Close Time (UTC)")


# -----------------------------
# MAIN
# -----------------------------
data = get_markets()

if data:
    markets = filter_today_markets(data)
    df = prepare_table(markets)

    st.write(f"### Total markets found: {len(df)}")

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No markets found for the next 24 hours.")
else:
    st.error("Failed to load data.")
