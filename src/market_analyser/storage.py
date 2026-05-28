from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .config import DATA_DIR, DB_PATH


def ensure_data_path() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_tables(db_path: Path | str = DB_PATH) -> None:
    ensure_data_path()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS instruments (
            instrument_id INTEGER PRIMARY KEY,
            market_type TEXT,
            symbol TEXT,
            normalized_symbol TEXT,
            display_name TEXT,
            is_active INTEGER,
            created_at TEXT
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS analysis_runs (
            run_id INTEGER PRIMARY KEY,
            instrument_id INTEGER,
            timeframe TEXT,
            start_date TEXT,
            end_date TEXT,
            overall_score REAL,
            sentiment_state TEXT,
            created_at TEXT
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS indicator_results (
            indicator_result_id INTEGER PRIMARY KEY,
            run_id INTEGER,
            indicator_key TEXT,
            indicator_name TEXT,
            indicator_value TEXT,
            signal_state TEXT,
            used_for TEXT,
            meaning TEXT,
            weight REAL,
            created_at TEXT
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS trade_signals (
            trade_signal_id INTEGER PRIMARY KEY,
            run_id INTEGER,
            target_price REAL,
            stop_loss REAL,
            take_profit REAL,
            prediction_score REAL,
            rank_order INTEGER,
            reasoning TEXT,
            created_at TEXT
        )
        '''
    )

    conn.commit()
    conn.close()


def init_db(db_path: Optional[Path | str] = None) -> None:
    create_tables(db_path or DB_PATH)
