from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Market Analyser", page_icon="📈", layout="wide")

st.title("Market Analyser — Starter")
st.write("This is a minimal starter app. Use the sidebar to select an instrument and timeframe.")

with st.sidebar:
    st.header("Controls")
    instrument = st.text_input("Symbol", value="AAPL")
    market_type = st.selectbox("Market Type", ["stock", "index", "crypto", "metal", "oil"]) 
    timeframe = st.selectbox("Timeframe", ["1d", "1h", "15m"]) 
    run = st.button("Run analysis")

if run:
    st.info("Analysis is not implemented yet. Review the specification and run the scaffolded modules.")
    st.write("Selected:", instrument, market_type, timeframe)
