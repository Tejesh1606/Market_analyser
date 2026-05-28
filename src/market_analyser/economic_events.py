from __future__ import annotations

import csv
import io
from typing import Iterable, Mapping, Any, List

import pandas as pd

from .storage import save_economic_events, load_economic_events


EVENT_COLUMNS = [
    "event_time",
    "currency",
    "event_name",
    "impact",
    "actual",
    "forecast",
    "previous",
    "notes",
    "source",
]


def normalize_event_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a row from CSV/text input into the storage schema."""
    return {
        "event_time": str(row.get("event_time") or row.get("time") or row.get("date") or ""),
        "currency": str(row.get("currency") or row.get("ccy") or row.get("symbol") or ""),
        "event_name": str(row.get("event_name") or row.get("event") or row.get("name") or ""),
        "impact": str(row.get("impact") or row.get("importance") or row.get("level") or ""),
        "actual": str(row.get("actual") or ""),
        "forecast": str(row.get("forecast") or ""),
        "previous": str(row.get("previous") or ""),
        "notes": str(row.get("notes") or row.get("note") or ""),
        "source": str(row.get("source") or "manual"),
    }


def parse_csv_text(csv_text: str) -> list[dict[str, Any]]:
    """Parse CSV text into normalized event rows.

    Expected columns (flexible): event_time,time,date,currency,event_name,event,impact,actual,forecast,previous,notes.
    """
    if not csv_text.strip():
        return []

    # Try pandas first for convenience, then fall back to csv.DictReader
    try:
        df = pd.read_csv(io.StringIO(csv_text))
        rows = df.fillna("").to_dict(orient="records")
    except Exception:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)

    return [normalize_event_row(r) for r in rows]


def import_events_from_csv_text(csv_text: str) -> int:
    rows = parse_csv_text(csv_text)
    if not rows:
        return 0
    return save_economic_events(rows)


def get_recent_events(limit: int = 50) -> list[dict[str, Any]]:
    return load_economic_events(limit=limit)


def to_dataframe(events: Iterable[Mapping[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(list(events))
