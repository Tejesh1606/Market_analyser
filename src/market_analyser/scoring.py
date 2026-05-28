from __future__ import annotations

from typing import List, Dict, Any


def score_signals(indicator_summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Produce ranked trade signals from indicator summaries.

    This is a stub: it aggregates by signal_score and returns empty trade suggestions.
    """
    # Sort indicators by score (placeholder)
    sorted_ind = sorted(indicator_summaries, key=lambda x: x.get("signal_score", 0.0), reverse=True)
    return [{
        "target_price": None,
        "stop_loss": None,
        "take_profit": None,
        "prediction_score": ind.get("signal_score", 0.0),
        "reasoning": f"Derived from {ind.get('indicator_key')}",
    } for ind in sorted_ind]
