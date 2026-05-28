from __future__ import annotations

import os
from typing import Optional

import requests


def _normalize_symbol(symbol: str) -> str:
    symbol_key = (symbol or "").upper().strip()
    if symbol_key in {"XAU", "XAUUSD", "GOLD"}:
        return "xau"
    if symbol_key in {"XAG", "XAGUSD", "SILVER"}:
        return "xag"
    if symbol_key in {"BTC", "BTCUSD", "BITCOIN"}:
        return "btc"
    return ""


def fetch_xau_api_quote(symbol: str, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 10) -> Optional[float]:
    """Fetch the current live price from XAU-API if the symbol is supported.

    Expected endpoints:
    - /price for xau
    - /xag-price for xag
    - /btc-price for btc
    """
    asset = _normalize_symbol(symbol)
    if not asset:
        return None

    base = (base_url or os.environ.get("XAU_API_BASE_URL") or "http://localhost:8085").rstrip("/")
    header_key = api_key or os.environ.get("XAU_API_KEY") or os.environ.get("API_KEY")
    endpoint = {
        "xau": "/price",
        "xag": "/xag-price",
        "btc": "/btc-price",
    }[asset]

    headers = {"X-API-Key": header_key} if header_key else {}
    try:
        resp = requests.get(f"{base}{endpoint}", headers=headers, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return None

    try:
        return float(payload.get("price"))
    except Exception:
        return None
