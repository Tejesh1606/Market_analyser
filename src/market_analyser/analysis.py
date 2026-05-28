from __future__ import annotations

from datetime import date
from datetime import datetime as _dt

import pandas as pd
import yfinance as yf

from .config import load_dotenv_file
from .storage import load_price_history, save_price_history
from .aliases import get_aliases
from .alpha_vantage import fetch_alpha_vantage_history


load_dotenv_file()


def fetch_price_history(
    symbol: str,
    start: date,
    end: date,
    interval: str = "1d",
    force_refresh: bool = False,
    provider: str = "auto",
) -> pd.DataFrame:
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

    # Fast path for intraday metal symbols: use the futures proxy directly.
    if interval != "1d" and symbol_key in {"XAU", "XAUUSD", "GOLD"}:
        try:
            proxy_history = yf.download(
                "GC=F",
                start=start_ts,
                end=end_ts,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception:
            proxy_history = pd.DataFrame()

        if proxy_history is not None and not proxy_history.empty:
            if isinstance(proxy_history.columns, pd.MultiIndex):
                proxy_history.columns = [str(level_0) for level_0, _level_1 in proxy_history.columns]
            proxy_history = proxy_history.reset_index()
            if "index" in proxy_history.columns:
                proxy_history = proxy_history.rename(columns={"index": "Date"})
            elif "Datetime" in proxy_history.columns:
                proxy_history = proxy_history.rename(columns={"Datetime": "Date"})
            proxy_history["Date"] = pd.to_datetime(proxy_history["Date"], errors="coerce")
            proxy_history = proxy_history.dropna(subset=["Date"])
            for column in columns:
                if column not in proxy_history.columns:
                    proxy_history[column] = pd.NA
            proxy_history = proxy_history[columns].sort_values("Date").reset_index(drop=True)
            if not proxy_history.empty:
                save_price_history(symbol_key, proxy_history)
                return proxy_history

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

    provider_key = (provider or "auto").strip().lower()

    # Prefer Alpha Vantage for FX-style symbols when an API key is available.
    if provider_key in {"auto", "alpha_vantage", "alphavantage", "av"}:
        av_history = fetch_alpha_vantage_history(symbol_key, start_ts, end_ts, interval=interval)
        if not av_history.empty:
            save_price_history(symbol_key, av_history)
            return av_history

    # attempt download for the requested symbol and alias/proxy fallbacks.
    history = pd.DataFrame()
    used_ticker = symbol_key
    download_order = list(aliases) + [symbol_key] if interval != "1d" and aliases else [symbol_key] + list(aliases)
    for candidate in download_order:
        try:
            tmp = yf.download(
                candidate,
                start=start_ts,
                end=end_ts,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception:
            tmp = pd.DataFrame()

        if tmp is None or tmp.empty:
            continue

        if interval != "1d" and aliases:
            # If the requested intraday interval still yields daily-shaped rows, keep looking.
            try:
                idx = pd.to_datetime(tmp.index, errors="coerce")
                if getattr(idx, "notna", None) is not None and len(idx) > 0:
                    looks_daily = bool((idx.hour == 0).all() and (idx.minute == 0).all() and (idx.second == 0).all())
                    if looks_daily:
                        continue
            except Exception:
                pass

        history = tmp
        used_ticker = candidate
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
