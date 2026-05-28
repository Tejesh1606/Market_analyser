from __future__ import annotations

from typing import List, Dict, Any, Optional

import pandas as pd


def _compute_atr(history: pd.DataFrame, period: int = 14) -> float:
    """Compute a simple ATR over the given history (returns last ATR value).

    Expects `High`, `Low`, `Close` columns.
    """
    h = history["High"].astype(float)
    l = history["Low"].astype(float)
    c = history["Close"].astype(float)
    tr1 = h - l
    tr2 = (h - c.shift(1)).abs()
    tr3 = (l - c.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return float(atr.iloc[-1])


def _recent_high_low(history: pd.DataFrame, lookback: int = 50) -> Dict[str, Optional[float]]:
    window = history.tail(lookback)
    if window.empty:
        return {"high": None, "low": None}
    high = float(window["High"].max())
    low = float(window["Low"].min())
    return {"high": high, "low": low}


def generate_trade_signals(
    symbol: str,
    price_history: pd.DataFrame,
    indicator_frame: pd.DataFrame,
    max_signals: int = 3,
) -> List[Dict[str, Any]]:
    """Generate ranked trade signals (target, stop_loss, take_profit, prediction_score).

    Strategy (heuristic):
    - Use SMA20 vs SMA50 for trend direction.
    - Use ATR for distance-based SL/TP levels.
    - Use recent highs/lows as support/resistance if they are on the correct side.
    - Produce `max_signals` candidates by scaling TP distance (conservative -> aggressive).
    - Compute a simple confidence score from trend, momentum (RSI), and volatility (ATR).

    Returns a list sorted by `prediction_score` descending.
    """
    if price_history is None or price_history.empty:
        return []

    last = price_history.iloc[-1]
    last_close = float(last["Close"])

    # ATR
    try:
        atr = _compute_atr(price_history, period=14)
    except Exception:
        atr = max(0.01, last_close * 0.01)

    # Trend via SMA
    sma20 = None
    sma50 = None
    if "SMA_20" in indicator_frame.columns:
        sma20 = float(indicator_frame["SMA_20"].dropna().iloc[-1])
    if "SMA_50" in indicator_frame.columns:
        sma50 = float(indicator_frame["SMA_50"].dropna().iloc[-1])

    if sma20 is not None and sma50 is not None:
        if sma20 > sma50:
            direction = "bull"
        elif sma20 < sma50:
            direction = "bear"
        else:
            direction = "neutral"
    else:
        direction = "neutral"

    # Support / resistance
    levels = _recent_high_low(price_history, lookback=50)
    resistance = levels.get("high")
    support = levels.get("low")

    # Momentum (RSI)
    rsi = None
    if "RSI_14" in indicator_frame.columns:
        rsi = float(indicator_frame["RSI_14"].dropna().iloc[-1])

    # Confidence components
    trend_score = 0.5
    if direction == "bull":
        trend_score = 1.0
    elif direction == "bear":
        trend_score = 0.0

    momentum_score = 0.5
    if rsi is not None:
        # map RSI to 0..1 where extreme values (away from 50) increase signal (but cap)
        momentum_score = min(1.0, abs(rsi - 50.0) / 50.0)

    volatility_factor = 1.0 / (1.0 + (atr / max(1e-6, last_close)))

    # Build base confidence
    confidence = 0.5 * trend_score + 0.35 * momentum_score + 0.15 * volatility_factor
    confidence = max(0.0, min(1.0, confidence))

    # Generate multiple TP levels (conservative -> aggressive)
    signals: List[Dict[str, Any]] = []

    # Define multipliers for TP distance from price using ATR
    multipliers = [1.0, 2.0, 3.0][:max_signals]
    for idx, m in enumerate(multipliers, start=1):
        if direction == "bull":
            # prefer using resistance if it's above close and within a reasonable range
            if resistance and resistance > last_close:
                target = resistance if resistance - last_close <= m * atr * 4 else last_close + m * atr
            else:
                target = last_close + m * atr

            stop_loss = support if support and support < last_close else last_close - 1.0 * atr
            take_profit = target
        elif direction == "bear":
            if support and support < last_close:
                target = support if last_close - support <= m * atr * 4 else last_close - m * atr
            else:
                target = last_close - m * atr

            stop_loss = resistance if resistance and resistance > last_close else last_close + 1.0 * atr
            take_profit = target
        else:
            # neutral: provide symmetric targets
            target = last_close + (m * atr)
            stop_loss = last_close - (1.0 * atr)
            take_profit = last_close + (m * atr)

        # Adjust prediction score by distance (closer targets tend to have higher confidence)
        distance = abs(target - last_close)
        distance_factor = 1.0 / (1.0 + (distance / max(1e-6, atr)))
        prediction_score = float(max(0.0, min(1.0, confidence * (0.6 + 0.4 * distance_factor))))

        signals.append(
            {
                "symbol": symbol,
                "target_price": float(target) if target is not None else None,
                "stop_loss": float(stop_loss) if stop_loss is not None else None,
                "take_profit": float(take_profit) if take_profit is not None else None,
                "prediction_score": prediction_score,
                "reasoning": f"direction={direction}; atr={atr:.4f}; confidence={confidence:.3f}; multiplier={m}",
                "rank_order": idx,
            }
        )

    # sort by prediction_score descending
    signals_sorted = sorted(signals, key=lambda x: x["prediction_score"], reverse=True)
    return signals_sorted


if __name__ == "__main__":
    # quick smoke test when run directly (will not fetch real data)
    import pandas as _pd

    df = _pd.DataFrame({
        "Date": [],
        "Open": [],
        "High": [],
        "Low": [],
        "Close": [],
        "Volume": [],
    })
    print("scoring module loaded")
