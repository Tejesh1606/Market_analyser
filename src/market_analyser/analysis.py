from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd


def fetch_price_history(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Fetch price history for `symbol` between `start` and `end`.

    This is a placeholder — replace with `yfinance` or another provider implementation.
    """
    # Return an empty frame with expected columns to avoid downstream errors
    cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    return pd.DataFrame(columns=cols)


def build_market_snapshot(symbol: str, history: pd.DataFrame):
    """Build a lightweight market snapshot from price history."""
    if history.empty:
        return None
    latest_close = float(history["Close"].dropna().iloc[-1])
    previous_close = float(history["Close"].dropna().iloc[-2]) if len(history) > 1 else latest_close
    return {
        "ticker": symbol,
        "latest_close": latest_close,
        "previous_close": previous_close,
        "change": latest_close - previous_close,
    }
