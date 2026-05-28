"""Simple smoke test runner for Market Analyser.

Run this script to verify core functionality: price fetching, caching,
indicator calculation, interpretation, scoring, and event import/save.

Usage:
    python scripts/run_smoke_tests.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure project root is on sys.path so `src` imports resolve when run from scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.market_analyser.analysis import fetch_price_history, build_market_snapshot
from src.market_analyser.indicators import calculate_indicators
from src.market_analyser.interpretation import interpret_indicators
from src.market_analyser.scoring import generate_trade_signals
from src.market_analyser.economic_events import parse_csv_text, import_events_from_csv_text
from src.market_analyser.storage import save_economic_events


def run_one(symbol: str, days: int = 90, max_signals: int = 3) -> dict:
    end = date.today()
    start = end - timedelta(days=days)

    history = fetch_price_history(symbol, start, end)
    # call twice to validate caching path
    history2 = fetch_price_history(symbol, start, end)

    indicators = calculate_indicators(history) if not history.empty else history
    interpretations = interpret_indicators(indicators) if not getattr(indicators, "empty", True) else []
    signals = generate_trade_signals(symbol, history, indicators, max_signals=max_signals)
    snapshot = build_market_snapshot(symbol, indicators)

    return {
        "symbol": symbol,
        "rows": len(history),
        "cached_rows": len(history2),
        "indicators_rows": len(indicators) if not getattr(indicators, "empty", True) else 0,
        "interpretations": len(interpretations),
        "signals": len(signals),
        "snapshot_ok": snapshot is not None,
    }


def test_events() -> dict:
    csv_text = (
        "event_time,currency,event_name,impact,actual,forecast,previous,notes\n"
        "2026-05-28 13:30,USD,Core PCE,High,0.3%,0.2%,0.1%,Inflation release\n"
    )
    parsed = parse_csv_text(csv_text)
    imported = import_events_from_csv_text(csv_text)
    manual_saved = save_economic_events(parsed)
    return {"parsed": len(parsed), "imported": imported, "manual_saved": manual_saved}


def main():
    results = {}

    # Symbols to smoke-test
    symbols = ["AAPL", "BTC-USD"]
    for s in symbols:
        try:
            results[s] = run_one(s)
        except Exception as e:
            results[s] = {"error": str(e)}

    # future-date edge case
    future_start = date.today() + timedelta(days=30)
    future_end = future_start + timedelta(days=10)
    future_history = fetch_price_history("AAPL", future_start, future_end)
    results["future_range"] = {"rows": len(future_history)}

    results["events"] = test_events()

    print(json.dumps(results, indent=2))

    # Basic checks: ensure we have data for at least one symbol and events imported
    any_data = any(v.get("rows", 0) > 0 for k, v in results.items() if k in symbols)
    events_ok = results["events"]["manual_saved"] >= 1

    if not any_data:
        print("ERROR: No price data found for test symbols.")
        sys.exit(2)
    if not events_ok:
        print("ERROR: Event import/save failed.")
        sys.exit(3)

    print("SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
