from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable, Mapping, Any

import pandas as pd

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

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS economic_events (
            event_id INTEGER PRIMARY KEY,
            event_time TEXT,
            currency TEXT,
            event_name TEXT,
            impact TEXT,
            actual TEXT,
            forecast TEXT,
            previous TEXT,
            notes TEXT,
            source TEXT,
            created_at TEXT
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS price_cache (
            symbol TEXT,
            price_date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume REAL,
            updated_at TEXT,
            PRIMARY KEY (symbol, price_date)
        )
        '''
    )

    conn.commit()
    conn.close()


def init_db(db_path: Optional[Path | str] = None) -> None:
    create_tables(db_path or DB_PATH)


def save_economic_events(events: Iterable[Mapping[str, Any]], db_path: Optional[Path | str] = None) -> int:
    """Insert or replace economic events and return the number of rows written."""
    ensure_data_path()
    conn = sqlite3.connect(str(db_path or DB_PATH))
    cur = conn.cursor()

    now = datetime.utcnow().isoformat(timespec="seconds")
    rows = []
    for event in events:
        rows.append(
            (
                event.get("event_time"),
                event.get("currency"),
                event.get("event_name"),
                event.get("impact"),
                event.get("actual"),
                event.get("forecast"),
                event.get("previous"),
                event.get("notes"),
                event.get("source", "manual"),
                now,
            )
        )

    cur.executemany(
        '''
        INSERT INTO economic_events (
            event_time, currency, event_name, impact, actual, forecast, previous, notes, source, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''' ,
        rows,
    )
    conn.commit()
    written = len(rows)
    conn.close()
    return written


def load_economic_events(limit: int = 100, db_path: Optional[Path | str] = None):
    """Load recent economic events as a list of dicts."""
    ensure_data_path()
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT event_time, currency, event_name, impact, actual, forecast, previous, notes, source, created_at
        FROM economic_events
        ORDER BY event_time DESC, event_id DESC
        LIMIT ?
        ''' ,
        (limit,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def save_price_history(symbol: str, history: pd.DataFrame, db_path: Optional[Path | str] = None) -> int:
    """Store price history for a symbol and return the number of rows written."""
    ensure_data_path()
    if history is None or history.empty:
        return 0

    create_tables(db_path or DB_PATH)
    conn = sqlite3.connect(str(db_path or DB_PATH))
    cur = conn.cursor()

    frame = history.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["Date"])
    if frame.empty:
        conn.close()
        return 0

    now = datetime.utcnow().isoformat(timespec="seconds")
    rows = []
    for _, row in frame.iterrows():
        rows.append(
            (
                symbol.upper().strip(),
                pd.Timestamp(row["Date"]).isoformat(),
                None if pd.isna(row.get("Open")) else float(row.get("Open")),
                None if pd.isna(row.get("High")) else float(row.get("High")),
                None if pd.isna(row.get("Low")) else float(row.get("Low")),
                None if pd.isna(row.get("Close")) else float(row.get("Close")),
                None if pd.isna(row.get("Adj Close")) else float(row.get("Adj Close")),
                None if pd.isna(row.get("Volume")) else float(row.get("Volume")),
                now,
            )
        )

    cur.executemany(
        '''
        INSERT OR REPLACE INTO price_cache (
            symbol, price_date, open, high, low, close, adj_close, volume, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        ,
        rows,
    )
    conn.commit()
    written = len(rows)
    conn.close()
    return written


def load_price_history(symbol: str, start_date=None, end_date=None, db_path: Optional[Path | str] = None) -> pd.DataFrame:
    """Load cached price history for a symbol as a normalized dataframe."""
    ensure_data_path()
    create_tables(db_path or DB_PATH)
    conn = sqlite3.connect(str(db_path or DB_PATH))

    query = [
        "SELECT price_date, open, high, low, close, adj_close, volume",
        "FROM price_cache",
        "WHERE symbol = ?",
    ]
    params: list[Any] = [symbol.upper().strip()]

    if start_date is not None:
        query.append("AND price_date >= ?")
        params.append(pd.Timestamp(start_date).isoformat())
    if end_date is not None:
        query.append("AND price_date <= ?")
        params.append(pd.Timestamp(end_date).isoformat())

    query.append("ORDER BY price_date ASC")
    frame = pd.read_sql_query("\n".join(query), conn, params=params)
    conn.close()

    if frame.empty:
        return pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"])

    frame = frame.rename(
        columns={
            "price_date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "adj_close": "Adj Close",
            "volume": "Volume",
        }
    )
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["Date"])
    return frame[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]].reset_index(drop=True)


def get_cached_symbols(db_path: Optional[Path | str] = None) -> list[str]:
    """Return list of distinct symbols in the price cache."""
    ensure_data_path()
    conn = sqlite3.connect(str(db_path or DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM price_cache")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def save_trade_signal(
    target_price: float,
    stop_loss: float,
    take_profit: float,
    prediction_score: Optional[float] = None,
    reasoning: Optional[str] = None,
    db_path: Optional[Path | str] = None,
) -> int:
    """Save a trade signal and return the new row id."""
    ensure_data_path()
    conn = sqlite3.connect(str(db_path or DB_PATH))
    cur = conn.cursor()
    now = datetime.utcnow().isoformat(timespec="seconds")
    cur.execute(
        '''
        INSERT INTO trade_signals (run_id, target_price, stop_loss, take_profit, prediction_score, rank_order, reasoning, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            None,
            None if target_price is None else float(target_price),
            None if stop_loss is None else float(stop_loss),
            None if take_profit is None else float(take_profit),
            None if prediction_score is None else float(prediction_score),
            None,
            reasoning or "",
            now,
        ),
    )
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid
