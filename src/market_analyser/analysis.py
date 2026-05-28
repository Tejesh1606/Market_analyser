from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from .storage import load_price_history, save_price_history


def fetch_price_history(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Fetch price history for `symbol` between `start` and `end`.

    Returns a normalized DataFrame with the columns expected by the rest of the app.
    """
    columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]

    cached_history = load_price_history(symbol, start, end)
    if not cached_history.empty:
        cached_dates = set(pd.to_datetime(cached_history["Date"], errors="coerce").dt.date.dropna())
        expected_days = pd.date_range(start=start, end=end, freq="B").date
        if all(day in cached_dates for day in expected_days):
            return cached_history

    try:
        history = yf.download(
            symbol,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        return pd.DataFrame(columns=columns)

    if history is None or history.empty:
        return pd.DataFrame(columns=columns)

    if isinstance(history.columns, pd.MultiIndex):
        history.columns = [str(level_0) for level_0, _level_1 in history.columns]

    history = history.reset_index()
    if "index" in history.columns:
        history = history.rename(columns={"index": "Date"})
    elif "Datetime" in history.columns:
        history = history.rename(columns={"Datetime": "Date"})

    if "Date" in history.columns:
        history["Date"] = pd.to_datetime(history["Date"], errors="coerce")
        history = history.dropna(subset=["Date"])

    for column in columns:
        if column not in history.columns:
            history[column] = pd.NA

    history = history[columns].sort_values("Date").reset_index(drop=True)

    if not history.empty:
        save_price_history(symbol, history)

    if not cached_history.empty:
        combined = pd.concat([cached_history, history], ignore_index=True)
        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
        combined = combined.dropna(subset=["Date"])
        combined = combined.drop_duplicates(subset=["Date"], keep="last")
        combined = combined.sort_values("Date").reset_index(drop=True)
        return combined

    return history


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
