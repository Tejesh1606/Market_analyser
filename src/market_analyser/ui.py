from __future__ import annotations

from datetime import date, timedelta
from typing import Callable

import streamlit as st


def render_dashboard(*, run_button_label: str = "Run analysis") -> None:
    st.title("Market Analyser — UI Stub")
    st.caption("This UI scaffold shows controls; analysis modules are placeholders.")

    with st.sidebar:
        st.header("Controls")
        symbol = st.text_input("Symbol", value="AAPL")
        market_type = st.selectbox("Market Type", ["stock", "index", "crypto", "metal", "oil"]) 
        timeframe = st.selectbox("Timeframe", ["1d", "1h", "15m"]) 
        start_date = st.date_input("Start date", value=date.today() - timedelta(days=365))
        end_date = st.date_input("End date", value=date.today())
        run = st.button(run_button_label)

    st.write("Selected:")
    st.write({"symbol": symbol, "market_type": market_type, "timeframe": timeframe, "start_date": start_date, "end_date": end_date})

    if run:
        st.info("Run pressed. Analysis modules are not yet implemented — see src/market_analyser for stubs.")
