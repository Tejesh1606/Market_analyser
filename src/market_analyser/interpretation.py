from __future__ import annotations

from typing import Dict, Any


def interpret_indicator(indicator_key: str, value: Any) -> Dict[str, Any]:
    """Return interpretation for a given indicator value.

    Placeholder implementation: returns a neutral interpretation.
    """
    return {
        "indicator_key": indicator_key,
        "indicator_value": value,
        "used_for": "(todo)",
        "meaning": "No interpretation implemented",
        "signal_state": "neutral",
        "signal_score": 0.0,
    }
