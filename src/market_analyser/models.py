from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class MarketSnapshot:
    ticker: str
    latest_close: float
    previous_close: float
    change: float
    change_percent: float
    average_volume: float
    volatility: float
    total_return: float
    as_of: Optional[date] = None


@dataclass
class IndicatorResult:
    indicator_key: str
    indicator_name: str
    indicator_value: Optional[float]
    signal_state: str  # 'positive'|'neutral'|'negative'
    meaning: str
    weight: float = 1.0


@dataclass
class AnalysisRun:
    run_id: Optional[int]
    symbol: str
    market_type: str
    timeframe: str
    start_date: Optional[date]
    end_date: Optional[date]
    overall_score: Optional[float] = None
