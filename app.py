import requests
import streamlit as st
from datetime import datetime

st.title("Kalshi - Today's Sports Markets")

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

def get_markets():
    params = {
        "status": "open",
        "limit": 1000
    }
    response = requests.get(BASE_URL, params=params)
    return response.json()

def filter_today(markets):
    today = datetime.utcnow().date()
    todays_markets = []

    for m in markets["markets"]:
        if "event_date" in m:
            event_date = datetime.fromisoformat(m["event_date"]).date()
            if event_date == today:
                todays_markets.append({
                    "title": m["title"],
                    "ticker": m["ticker"],
                    "yes_price": m["yes_ask"],
                    "no_price": m["no_ask"]
                })
    return todays_markets

data = get_markets()
today_games = filter_today(data)

st.write(f"Total games today: {len(today_games)}")

for game in today_games:
    st.write(game)
