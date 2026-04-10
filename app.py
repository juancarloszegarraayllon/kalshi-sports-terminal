import streamlit as st
import pandas as pd
import time
from datetime import timezone
import tempfile

st.set_page_config(page_title="OddsIQ Debug", layout="wide")

st.markdown("<div style='text-align:center;font-size:80px;color:#00ff00;font-weight:800;margin:2rem 0;'>OddsIQ</div>", unsafe_allow_html=True)

st.markdown("### 🚨 Debug Mode - Let's see what's happening")

if st.button("🔄 Start Loading Markets (click this)", type="primary", use_container_width=True):
    st.session_state["start_clicked"] = True

if st.session_state.get("start_clicked"):

    with st.spinner("Step 1: Creating Kalshi client..."):
        try:
            from kalshi_python_sync import Configuration, KalshiClient
            key_id = st.secrets["KALSHI_API_KEY_ID"]
            key_str = st.secrets["KALSHI_PRIVATE_KEY"]
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".pem") as f:
                f.write(key_str)
                pem = f.name
            
            cfg = Configuration()
            cfg.api_key_id = key_id
            cfg.private_key_pem_path = pem
            client = KalshiClient(cfg)
            st.success("✅ Kalshi client created successfully")
        except Exception as e:
            st.error(f"❌ Client creation failed: {e}")
            st.stop()

    with st.spinner("Step 2: Fetching events from Kalshi (this is the slow part)..."):
        try:
            events = []
            cursor = None
            progress = st.progress(0)

            for i in range(15):   # limit to 15 pages for testing
                resp = client.get_events(
                    limit=100, 
                    status="open", 
                    with_nested_markets=True, 
                    cursor=cursor
                ).to_dict()
                
                batch = resp.get("events", [])
                if not batch:
                    break
                    
                events.extend(batch)
                cursor = resp.get("cursor") or resp.get("next_cursor")
                if not cursor:
                    break
                    
                progress.progress(min(1.0, (i+1)/15), text=f"Loaded {len(events)} events...")
                time.sleep(0.1)

            progress.empty()
            st.success(f"✅ Fetched {len(events)} events successfully!")

            df = pd.DataFrame(events)
            st.write(f"DataFrame shape: {df.shape}")
            if not df.empty:
                st.dataframe(df[["event_ticker", "title", "category"]].head(10))
            
        except Exception as e:
            st.error(f"❌ Fetching failed: {type(e).__name__} - {e}")

    st.info("If you see the success message above, the core fetch works. We can now add back your cards.")

else:
    st.info("Click the big button above to test the loading process.")

st.markdown("---")
st.caption("Debug version - tell me exactly what you see after clicking the button (spinner forever? error message? success?)")
