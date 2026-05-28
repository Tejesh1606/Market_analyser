"""Common ticker alias mappings for instruments where Yahoo uses different symbols.

Each key is an uppercase user-facing token and the value is a list of candidate
Yahoo tickers to try (in order) when fetching price data.
"""

ALIASES: dict[str, list[str]] = {
    # Metals
    "XAU": ["GC=F"],
    "XAUUSD": ["GC=F"],
    "GOLD": ["GC=F"],
    "XAG": ["SI=F"],
    "SILVER": ["SI=F"],

    # Energy
    "OIL": ["CL=F"],
    "WTI": ["CL=F"],
    "BRENT": ["BZ=F"],

    # Forex (common formats)
    "EURUSD": ["EURUSD=X"],
    "GBPUSD": ["GBPUSD=X"],
    "USDJPY": ["JPY=X"],

    # Crypto
    "BTC": ["BTC-USD"],
    "BTCUSD": ["BTC-USD"],
    "ETH": ["ETH-USD"],
    "ETHUSD": ["ETH-USD"],

    # Index aliases
    "SPX": ["^GSPC"],
    "SP500": ["^GSPC"],
    "DOW": ["^DJI"],
}


def get_aliases(symbol: str) -> list[str]:
    if not symbol:
        return []
    return ALIASES.get(symbol.upper().strip(), [])
