"""Check which Yahoo tickers return price data via yfinance."""
from datetime import date, timedelta
import yfinance as yf


def main():
    symbols = ["XAUUSD", "XAU", "GC=F", "XAUUSD=X", "XAU=X"]
    end = date.today()
    start = end - timedelta(days=60)
    for s in symbols:
        try:
            df = yf.download(s, start=start, end=end, progress=False, threads=False)
            print(f"{s}: rows={len(df)}")
        except Exception as e:
            print(f"{s}: error={e}")


if __name__ == "__main__":
    main()
