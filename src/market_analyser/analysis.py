from __future__ import annotations

from datetime import date
from datetime import datetime as _dt

import pandas as pd
import yfinance as yf

from .storage import load_price_history, save_price_history
from .aliases import get_aliases


def fetch_price_history(symbol: str, start: date, end: date, interval: str = "1d", force_refresh: bool = False) -> pd.DataFrame:
    """Fetch price history for `symbol` between `start` and `end`.

    Returns a normalized DataFrame with the columns expected by the rest of the app.
    """
    columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    # normalize start/end to pandas Timestamps so intraday datetimes work
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    today = pd.Timestamp.utcnow().date()

    if start_ts.date() > today:
        return pd.DataFrame(columns=columns)

    if end_ts.date() > today:
        end_ts = pd.Timestamp(today)

    if start_ts > end_ts:
        return pd.DataFrame(columns=columns)

    symbol = (symbol or "").strip()
    if not symbol:
        return pd.DataFrame(columns=columns)

    symbol_key = symbol.upper().strip()

    # resolve aliases from centralized registry
    aliases = get_aliases(symbol_key)

    cached_history = load_price_history(symbol_key, start_ts, end_ts)
    if not force_refresh and not cached_history.empty:
        # only perform the business-day completeness check for daily intervals
        if interval == "1d":
            cached_dates = set(pd.to_datetime(cached_history["Date"], errors="coerce").dt.date.dropna())
            expected_days = pd.date_range(start=start, end=end, freq="B").date
            if all(day in cached_dates for day in expected_days):
                return cached_history
        else:
            # for intraday intervals just return cached if non-empty
            return cached_history

    # attempt download for the requested symbol, then fallback to aliases if available
    history = pd.DataFrame()
    used_ticker = symbol_key
    try:
        history = yf.download(
            symbol_key,
            start=start_ts,
            end=end_ts,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        history = pd.DataFrame()

    if history is None or history.empty:
        # try alias fallbacks
        for alias in aliases:
            try:
                tmp = yf.download(
                    alias,
                    start=start,
                    end=end,
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    threads=False,
                )
            except Exception:
                tmp = pd.DataFrame()
            if tmp is not None and not tmp.empty:
                history = tmp
                used_ticker = alias
                break

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
        # save using the original requested symbol key so future lookups use the cache
        save_price_history(symbol_key, history)

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
