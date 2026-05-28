from __future__ import annotations

import streamlit as st

# Check required optional modules early and show a friendly message if missing.
try:
	import yfinance  # noqa: F401
except Exception as exc:  # pragma: no cover - runtime safety
	st.set_page_config(page_title="Market Analyser", page_icon="📈", layout="wide")
	st.title("Market Analyser — Missing dependency")
	st.error(
		"Required analysis modules missing: No module named 'yfinance'.\n"
		"Install dependencies with `python -m pip install -r requirements.txt`\n"
		"or `python -m pip install yfinance` and re-run the app."
	)
	st.stop()

from src.market_analyser.ui import render_dashboard

st.set_page_config(page_title="Market Analyser", page_icon="📈", layout="wide")

render_dashboard()
