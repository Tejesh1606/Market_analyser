from __future__ import annotations

import pandas as pd


def calculate_indicators(history: pd.DataFrame) -> pd.DataFrame:
    """Calculate common technical indicators and append them to the DataFrame.

    Expected input columns: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.
    Adds columns: `SMA_20`, `SMA_50`, `EMA_12`, `EMA_26`, `MACD`, `MACD_SIGNAL`,
    `MACD_HIST`, `RSI_14`, `ATR_14`, `BB_UPPER`, `BB_MIDDLE`, `BB_LOWER`, `VOLUME_MA_20`.
    """
    if history is None or history.empty:
        return history

    df = history.copy()
    # Ensure numeric types
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Moving averages
    df["SMA_20"] = df["Close"].rolling(window=20, min_periods=1).mean()
    df["SMA_50"] = df["Close"].rolling(window=50, min_periods=1).mean()

    # EMAs for MACD
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

    # EMA 13 for Bulls/Bears power
    df["EMA_13"] = df["Close"].ewm(span=13, adjust=False).mean()
    # Bulls Power = High - EMA(13); Bears Power = Low - EMA(13)
    df["BULLS_POWER"] = df["High"] - df["EMA_13"]
    df["BEARS_POWER"] = df["Low"] - df["EMA_13"]

    # RSI (14)
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    df["RSI_14"] = 100 - (100 / (1 + rs))
    df["RSI_14"] = df["RSI_14"].bfill().fillna(50)

    # ATR (14)
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR_14"] = tr.rolling(window=14, min_periods=1).mean()

    # Bollinger Bands (20,2)
    bb_mid = df["Close"].rolling(window=20, min_periods=1).mean()
    bb_std = df["Close"].rolling(window=20, min_periods=1).std()
    df["BB_MIDDLE"] = bb_mid
    df["BB_UPPER"] = bb_mid + 2 * bb_std
    df["BB_LOWER"] = bb_mid - 2 * bb_std

    # Volume moving average
    if "Volume" in df.columns:
        df["VOLUME_MA_20"] = df["Volume"].rolling(window=20, min_periods=1).mean()

    # Stochastic Oscillator (14,3)
    low14 = df["Low"].rolling(window=14, min_periods=1).min()
    high14 = df["High"].rolling(window=14, min_periods=1).max()
    df["STOCH_K"] = ((df["Close"] - low14) / (high14 - low14).replace(0, pd.NA)) * 100
    # ensure STOCH_K is numeric (replace pd.NA with np.nan) to allow rolling ops
    df["STOCH_K"] = pd.to_numeric(df["STOCH_K"], errors="coerce")
    df["STOCH_D"] = df["STOCH_K"].rolling(window=3, min_periods=1).mean()
    df["STOCH_DEV"] = df["STOCH_K"] - df["STOCH_D"]

    return df
