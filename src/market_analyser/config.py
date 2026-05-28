from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "market_analyser.db"


def load_dotenv_file(dotenv_path: Path | None = None) -> None:
	"""Load simple KEY=VALUE pairs from a local .env file if present.

	Keeps the app self-contained without requiring python-dotenv.
	"""
	path = dotenv_path or (PROJECT_ROOT / ".env")
	if not path.exists():
		return

	for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value

DEFAULT_TIMEFRAME = "1d"
DEFAULT_LOOKBACK_DAYS = 365
DEFAULT_INDICATORS = ["SMA_20", "SMA_50", "RSI_14", "MACD", "ATR_14"]
