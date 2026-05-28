from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

from .storage import get_cached_symbols, load_price_history
from .indicators import calculate_indicators
from .config import DATA_DIR


MODEL_DIR = DATA_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "trade_predictor.joblib"
MODEL_META = MODEL_DIR / "trade_predictor_meta.json"


def _build_examples_for_symbol(symbol: str, horizon: int = 5) -> pd.DataFrame:
    df = load_price_history(symbol)
    if df.empty:
        return pd.DataFrame()
    # ensure numeric columns are coerced for indicator calculations
    for col in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    ind = calculate_indicators(df)
    ind = ind.sort_values("Date").reset_index(drop=True)

    rows = []
    for i in range(len(ind) - horizon - 1):
        cur = ind.iloc[i]
        future = ind.iloc[i + 1 : i + 1 + horizon]
        if future.empty:
            continue
        cur_close = float(cur.get("Close", np.nan))
        if np.isnan(cur_close) or cur_close == 0:
            continue
        future_max = float(future["High"].max())
        future_min = float(future["Low"].min())
        future_close = float(future["Close"].iloc[-1])

        tp_pct = (future_max / cur_close) - 1.0
        sl_pct = (future_min / cur_close) - 1.0
        ret_pct = (future_close / cur_close) - 1.0

        features = cur.drop(labels=["Date"]).to_dict()
        features.update({"symbol": symbol, "tp_pct": tp_pct, "sl_pct": sl_pct, "ret_pct": ret_pct})
        rows.append(features)

    return pd.DataFrame(rows)


def build_dataset(horizon: int = 5, min_rows_per_symbol: int = 50) -> tuple[pd.DataFrame, pd.DataFrame]:
    symbols = get_cached_symbols()
    frames = []
    for s in symbols:
        df = _build_examples_for_symbol(s, horizon=horizon)
        if len(df) >= min_rows_per_symbol:
            frames.append(df)
    if not frames:
        return pd.DataFrame(), pd.DataFrame()
    all_df = pd.concat(frames, ignore_index=True, sort=False)

    # drop non-numeric columns and NaNs in targets
    target_cols = ["tp_pct", "sl_pct", "ret_pct"]
    X = all_df.drop(columns=target_cols + ["symbol"], errors="ignore").select_dtypes(include=["number"]).fillna(0)
    y = all_df[target_cols].fillna(0)
    return X, y


def train_model(horizon: int = 5, n_estimators: int = 50, test_size: float = 0.2, random_state: int = 42) -> dict:
    X, y = build_dataset(horizon=horizon)
    if X.empty or y.empty:
        raise RuntimeError("No training data available — ensure price cache contains enough symbols and rows.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    base = RandomForestRegressor(n_estimators=n_estimators, n_jobs=-1, random_state=random_state)
    model = MultiOutputRegressor(base)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    scores = {
        "r2": r2_score(y_test, preds, multioutput="uniform_average"),
        "mae": mean_absolute_error(y_test, preds),
    }

    joblib.dump({"model": model, "features": list(X.columns), "horizon": horizon}, MODEL_PATH)
    MODEL_META.write_text(json.dumps({"features": list(X.columns), "horizon": horizon, "scores": scores}, indent=2))

    return {"model_path": str(MODEL_PATH), "meta_path": str(MODEL_META), "scores": scores, "n_samples": len(X)}


def load_trained_model() -> Optional[dict]:
    if not MODEL_PATH.exists():
        return None
    payload = joblib.load(MODEL_PATH)
    return payload


def predict_for_latest(symbol: str) -> dict:
    payload = load_trained_model()
    if payload is None:
        raise RuntimeError("No trained model present. Run training first.")
    model = payload["model"]
    features = payload["features"]

    df = load_price_history(symbol)
    if df.empty:
        raise RuntimeError("No cached price history for symbol")
    ind = calculate_indicators(df)
    latest = ind.sort_values("Date").iloc[-1:]
    X = latest.drop(columns=["Date"]).select_dtypes(include=["number"]).reindex(columns=features, fill_value=0)
    preds = model.predict(X)
    tp_pct, sl_pct, ret_pct = preds[0]
    close = float(latest["Close"].iloc[0])
    return {"pred_tp": close * (1 + tp_pct), "pred_sl": close * (1 + sl_pct), "pred_ret": ret_pct}
