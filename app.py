from __future__ import annotations

import streamlit as st
import sys

# Check required optional modules early and show a friendly message if missing.
try:
	import yfinance  # noqa: F401
except Exception as exc:  # pragma: no cover - runtime safety
	st.set_page_config(page_title="Market Analyser", page_icon="📈", layout="wide")
	st.title("Market Analyser — Missing dependency")
	exe = sys.executable or "python"
	pip_cmd = f'"{exe}" -m pip install yfinance'
	st.error(
		"Required analysis modules missing: No module named 'yfinance'."
	)
	st.markdown(
		"**Quick fixes:**\n"
		f"- Install into the interpreter Streamlit is using: `{pip_cmd}`\n"
		"- Or install all dependencies: `python -m pip install -r requirements.txt`\n"
	)
	with st.expander("Interpreter info"):
		st.write({"sys_executable": exe, "argv": sys.argv})
	st.stop()

from src.market_analyser.ui import render_dashboard

st.set_page_config(page_title="Market Analyser", page_icon="📈", layout="wide")

render_dashboard()
