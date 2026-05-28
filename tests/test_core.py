from datetime import date, timedelta

from src.market_analyser.analysis import fetch_price_history
from src.market_analyser.indicators import calculate_indicators
from src.market_analyser.interpretation import interpret_indicators
from src.market_analyser.scoring import generate_trade_signals
from src.market_analyser.economic_events import parse_csv_text
from src.market_analyser.storage import save_economic_events


def test_fetch_price_history_aapl():
    end = date.today()
    start = end - timedelta(days=30)
    df = fetch_price_history("AAPL", start, end)
    assert hasattr(df, "empty")
    assert len(df) >= 1


def test_indicators_and_signals():
    end = date.today()
    start = end - timedelta(days=60)
    df = fetch_price_history("AAPL", start, end)
    ind = calculate_indicators(df)
    assert len(ind) == len(df)
    interpretations = interpret_indicators(ind)
    signals = generate_trade_signals("AAPL", df, ind, max_signals=2)
    assert isinstance(signals, list)


def test_events_import_and_save():
    csv_text = (
        "event_time,currency,event_name,impact,actual,forecast,previous,notes\n"
        "2026-05-28 13:30,USD,Core PCE,High,0.3%,0.2%,0.1%,Inflation release\n"
    )
    rows = parse_csv_text(csv_text)
    written = save_economic_events(rows)
    assert written >= 1
