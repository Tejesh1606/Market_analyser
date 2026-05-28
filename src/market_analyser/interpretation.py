from __future__ import annotations

from typing import Dict, Any, List

def interpret_indicator_single(indicator_key: str, indicator_value: Any) -> Dict[str, Any]:
    """Interpret a single indicator value and return a structured explanation.

    Returns: {indicator_key, indicator_value, used_for, meaning, signal_state, signal_score}
    """
    used_for = "General"
    meaning = "No interpretation available"
    signal_state = "neutral"
    score = 0.0

    try:
        val = float(indicator_value)
    except Exception:
        val = None

    key = indicator_key.upper()
    if key in ("SMA_20", "SMA_50"):
        used_for = "Trend identification"
        meaning = f"Moving average value: {indicator_value}"
        signal_state = "neutral"
        score = 0.5

    if key == "RSI_14":
        used_for = "Momentum (overbought/oversold)"
        if val is None:
            meaning = "No value"
            signal_state = "neutral"
            score = 0.0
        elif val < 30:
            meaning = f"Oversold (RSI={val:.1f}) — possible buy signal"
            signal_state = "positive"
            score = min(1.0, (30 - val) / 30)
        elif val > 70:
            meaning = f"Overbought (RSI={val:.1f}) — caution for longs"
            signal_state = "negative"
            score = min(1.0, (val - 70) / 30)
        else:
            meaning = f"Neutral momentum (RSI={val:.1f})"
            signal_state = "neutral"
            score = 0.5

    if key == "MACD":
        used_for = "Momentum / trend change"
        if val is None:
            meaning = "No MACD value"
            signal_state = "neutral"
            score = 0.0
        elif val > 0:
            meaning = f"MACD positive ({val:.4f}) — bullish bias"
            signal_state = "positive"
            score = min(1.0, val / (abs(val) + 1.0))
        else:
            meaning = f"MACD negative ({val:.4f}) — bearish bias"
            signal_state = "negative"
            score = min(1.0, abs(val) / (abs(val) + 1.0))

    if key == "MACD_HIST":
        used_for = "Momentum acceleration"
        if val is None:
            signal_state = "neutral"
            score = 0.0
        elif val > 0:
            meaning = f"MACD histogram positive ({val:.4f}) — increasing bullish momentum"
            signal_state = "positive"
            score = min(1.0, val / (abs(val) + 1.0))
        else:
            meaning = f"MACD histogram negative ({val:.4f}) — increasing bearish momentum"
            signal_state = "negative"
            score = min(1.0, abs(val) / (abs(val) + 1.0))

    if key == "ATR_14":
        used_for = "Volatility (distance for SL/TP)"
        if val is None:
            meaning = "No ATR"
            score = 0.0
            signal_state = "neutral"
        else:
            meaning = f"ATR={val:.4f} (higher means wider SL recommended)"
            signal_state = "neutral"
            score = 0.5

    if key.startswith("BB_"):
        used_for = "Volatility / mean reversion"
        meaning = f"Bollinger band value: {indicator_value}"
        signal_state = "neutral"
        score = 0.5

    if key == "VOLUME_MA_20":
        used_for = "Volume confirmation"
        meaning = f"Volume MA={indicator_value}"
        signal_state = "neutral"
        score = 0.5

    return {
        "indicator_key": indicator_key,
        "indicator_value": indicator_value,
        "used_for": used_for,
        "meaning": meaning,
        "signal_state": signal_state,
        "signal_score": float(score),
    }


def interpret_indicators(indicator_frame: 'pandas.DataFrame') -> List[Dict[str, Any]]:
    """Create a summary interpretation for multiple indicators based on the latest row."""
    import pandas as pd

    if indicator_frame is None or indicator_frame.empty:
        return []

    last = indicator_frame.iloc[-1]
    keys_of_interest = [
        "SMA_20",
        "SMA_50",
        "RSI_14",
        "MACD",
        "MACD_HIST",
        "ATR_14",
        "BB_UPPER",
        "BB_MIDDLE",
        "BB_LOWER",
        "VOLUME_MA_20",
    ]
    summary = []
    order = 1
    for k in keys_of_interest:
        val = None
        if k in last.index:
            try:
                val = last[k]
            except Exception:
                val = None
        entry = interpret_indicator_single(k, val)
        entry["priority_order"] = order
        order += 1
        summary.append(entry)

    # Additional cross-indicator interpretation: SMA crossover
    try:
        s20 = float(last.get("SMA_20", float('nan')))
        s50 = float(last.get("SMA_50", float('nan')))
        if not pd.isna(s20) and not pd.isna(s50):
            if s20 > s50:
                summary.insert(0, {
                    "indicator_key": "SMA_CROSS",
                    "indicator_value": f"{s20:.4f} > {s50:.4f}",
                    "used_for": "Trend",
                    "meaning": "Short MA above long MA — bullish trend",
                    "signal_state": "positive",
                    "signal_score": 0.9,
                    "priority_order": 0,
                })
            elif s20 < s50:
                summary.insert(0, {
                    "indicator_key": "SMA_CROSS",
                    "indicator_value": f"{s20:.4f} < {s50:.4f}",
                    "used_for": "Trend",
                    "meaning": "Short MA below long MA — bearish trend",
                    "signal_state": "negative",
                    "signal_score": 0.9,
                    "priority_order": 0,
                })
    except Exception:
        pass

    return summary
