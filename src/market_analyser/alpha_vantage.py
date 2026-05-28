from __future__ import annotations

import os
from datetime import date
from io import StringIO
from typing import Optional

import pandas as pd
import requests

from .config import load_dotenv_file


ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"


def _alpha_vantage_key() -> Optional[str]:
    load_dotenv_file()
    return os.environ.get("alpha_vantage_free_key") or os.environ.get("ALPHA_VANTAGE_API_KEY")


def _symbol_to_fx_pair(symbol: str) -> tuple[Optional[str], Optional[str]]:
    symbol_key = (symbol or "").upper().strip()
    if not symbol_key:
        return None, None

    # Common cases for forex and spot-metal style symbols.
    if symbol_key == "XAUUSD":
        return "XAU", "USD"
    if symbol_key == "XAGUSD":
        return "XAG", "USD"
    if len(symbol_key) == 6 and symbol_key.isalnum():
        return symbol_key[:3], symbol_key[3:]
    return None, None


def fetch_alpha_vantage_history(symbol: str, start: date | pd.Timestamp, end: date | pd.Timestamp, interval: str = "1d") -> pd.DataFrame:
    """Fetch history from Alpha Vantage using FX intraday/daily endpoints when possible.

    Returns an empty DataFrame if the symbol is not supported or the API key is missing.
    """
    api_key = _alpha_vantage_key()
    if not api_key:
        return pd.DataFrame()

    from_currency, to_currency = _symbol_to_fx_pair(symbol)
    if not from_currency or not to_currency:
        return pd.DataFrame()

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    params: dict[str, str] = {
        "function": "FX_DAILY" if interval == "1d" else "FX_INTRADAY",
        "from_symbol": from_currency,
        "to_symbol": to_currency,
        "apikey": api_key,
        "outputsize": "full",
    }
    if interval != "1d":
        params["interval"] = interval

    try:
        resp = requests.get(ALPHA_VANTAGE_BASE, params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return pd.DataFrame()

    # Alpha Vantage uses different keys by endpoint / interval.
    time_series_key = next((k for k in payload.keys() if "Time Series" in k), None)
    if not time_series_key or time_series_key not in payload:
        return pd.DataFrame()

    rows = []
    for timestamp_str, values in payload[time_series_key].items():
        try:
            dt = pd.Timestamp(timestamp_str)
        except Exception:
            continue
        if dt < start_ts or dt > end_ts:
            continue
        rows.append(
            {
                "Date": dt,
                "Open": values.get("1. open"),
                "High": values.get("2. high"),
                "Low": values.get("3. low"),
                "Close": values.get("4. close"),
                "Adj Close": values.get("4. close"),
                "Volume": values.get("5. volume", 0),
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("Date").reset_index(drop=True)
