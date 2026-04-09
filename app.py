import streamlit as st
import pandas as pd
import tempfile

st.set_page_config(page_title="Kalshi Debug", layout="wide")
st.title("Kalshi API Debug")

# --- Connect ---
try:
    from kalshi_python_sync import Configuration, KalshiClient

    api_key_id = st.secrets["KALSHI_API_KEY_ID"]
    private_key_str = st.secrets["KALSHI_PRIVATE_KEY"]

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
        f.write(private_key_str)
        pem_path = f.name

    cfg = Configuration()
    cfg.api_key_id = api_key_id
    cfg.private_key_pem_path = pem_path
    client = KalshiClient(cfg)
    st.success("✅ Connected to Kalshi API")

except Exception as e:
    st.error(f"❌ Connection failed: {e}")
    st.stop()

# --- Fetch ALL events, no filtering ---
try:
    response = client.get_events(limit=200, status="open")
    events = response.to_dict().get("events", [])
    st.write(f"### Total events returned: {len(events)}")

    if not events:
        st.warning("API returned 0 events. Check your API key permissions.")
        st.stop()

    df = pd.DataFrame(events)

    st.write("### Column names:")
    st.write(list(df.columns))

    st.write("### First 5 events (all columns):")
    st.dataframe(df.head(5))

    st.write("### All event tickers + categories + titles:")
    cols = [c for c in ["event_ticker", "category", "title"] if c in df.columns]
    st.dataframe(df[cols].head(50))

except Exception as e:
    st.error(f"❌ Fetch failed: {e}")
