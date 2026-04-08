# --- App Layout ---
st.write("### Market Explorer")

# The Search Bar
search_query = st.text_input("🔍 Search", placeholder="Search by team, league, or event...")

df = fetch_all_markets()

if not df.empty:
    # Reactive Search Filtering
    if search_query:
        df = df[
            df['title'].str.contains(search_query, case=False, na=False) |
            df['ticker'].str.contains(search_query, case=False, na=False)
        ]

    # Identification of Sports vs Other (using tickers as we discussed)
    sport_prefixes = ('NBA', 'MLB', 'NFL', 'NHL', 'SOC', 'TEN', 'KX')
    is_sports = df['ticker'].str.startswith(sport_prefixes, na=False) | \
                df['title'].str.contains('vs|score|win', case=False, na=False)
    
    df_sports = df[is_sports].copy()
    df_other = df[~is_sports].copy()

    # (Add your percentage and time formatting here as in previous steps)

    tab1, tab2 = st.tabs(["🏆 Sports", "📈 General"])
    
    with tab1:
        if df_sports.empty:
            st.info("No sports matches found for this search.")
        else:
            st.dataframe(df_sports[["title", "Prob %", "Ends (UTC)"]], use_container_width=True, hide_index=True)

    with tab2:
        if df_other.empty:
            st.info("No general markets found for this search.")
        else:
            st.dataframe(df_other[["title", "Prob %", "Ends (UTC)"]], use_container_width=True, hide_index=True)
