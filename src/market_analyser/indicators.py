from __future__ import annotations

import pandas as pd


def calculate_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Append basic indicator columns to `history` and return the frame.

    This is intentionally minimal; implement concrete formulas later.
    """
    if history.empty:
        return history

    df = history.copy()
    if "Close" not in df.columns:
        return df

    # Example placeholders; real calculations should be applied here
    df["SMA_20"] = df["Close"].rolling(window=20, min_periods=1).mean()
    df["SMA_50"] = df["Close"].rolling(window=50, min_periods=1).mean()
    return df
