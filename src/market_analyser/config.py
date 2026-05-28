from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "market_analyser.db"

DEFAULT_TIMEFRAME = "1d"
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_INDICATORS = ["SMA_20", "SMA_50", "RSI_14", "MACD", "ATR_14"]
