from datetime import date, timedelta
from src.market_analyser.analysis import fetch_price_history

end = date.today()
start = end - timedelta(days=60)

for s in ['XAUUSD', 'XAU', 'GC=F']:
    df = fetch_price_history(s, start, end)
    print(f"{s}: rows={len(df)}")
