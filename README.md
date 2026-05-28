# Market Analyser

A local-first market analysis app built with Streamlit. It helps you inspect price action, interpret technical indicators, rank trade ideas, and keep an economic events calendar alongside the analysis.

## What it does

- Pulls daily market data with `yfinance`
- Calculates and interprets technical indicators
- Ranks trade suggestions with target, stop loss, take profit, and confidence
- Shows price charts, indicator charts, and a sentiment-style summary
- Stores economic events locally in SQLite
- Caches downloaded price history so repeated runs are faster
- Runs fully on your machine, no hosting required

## Main features

### Market analysis
- Symbol input for stocks, indices, crypto, metals, and oil-style tickers
- Date range selection
- Live data download and local price caching
- Snapshot metrics such as latest close, change, percent change, and volatility

### Indicators
The app currently calculates and interprets:
- `SMA_20`
- `SMA_50`
- `EMA_12`
- `EMA_26`
- `MACD`
- `MACD_SIGNAL`
- `MACD_HIST`
- `BULLS_POWER`
- `BEARS_POWER`
- `RSI_14`
- `ATR_14`
- `BB_MIDDLE`
- `BB_UPPER`
- `BB_LOWER`
- `VOLUME_MA_20`
- `STOCH_K`
- `STOCH_D`
- `STOCH_DEV`

### Trade suggestions
The app generates ranked suggestions with:
- target price
- stop loss
- take profit
- prediction score / confidence
- reasoning based on the current indicator mix

### Economic calendar
- Calendar-style local event view
- Manual event entry with date and time
- CSV paste or CSV upload for bulk import
- Local SQLite storage for reuse later

## Tech stack

- [Streamlit](https://streamlit.io/) — web UI
- [Plotly](https://plotly.com/python/) — interactive charts
- [Pandas](https://pandas.pydata.org/) — tabular data and calculations
- [NumPy](https://numpy.org/) — numeric helpers
- [yfinance](https://github.com/ranaroussi/yfinance) — market data download
- SQLite — local persistence for events and cached prices

## Project structure

```text
app.py
src/market_analyser/
  analysis.py
  config.py
  economic_events.py
  indicators.py
  interpretation.py
  models.py
  scoring.py
  storage.py
  ui.py
```

## Requirements

- Python 3.10+
- Internet access for live market downloads
- Windows, macOS, or Linux

## Setup

### 1) Create a virtual environment

```powershell
python -m venv .venv
```

### 2) Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks scripts, run:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

### 3) Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the app

```powershell
streamlit run app.py
```

## How to use it

### Market analysis flow
1. Open the app.
2. Enter a symbol such as `AAPL`.
3. Choose a start and end date.
4. Click **Run analysis**.
5. Review:
   - price chart
   - indicator chart
   - indicator explanations
   - ranked trade suggestions
   - summary counts

### Economic events flow
1. Open the economic calendar panel.
2. Use the month controls to move across dates.
3. Click a day to inspect its agenda.
4. Add a new event using the manual form.
5. Or paste/upload CSV data to import many events at once.

### CSV format for events
Use this header:

```csv
event_time,currency,event_name,impact,actual,forecast,previous,notes
```

Example:

```csv
2026-05-28 13:30,USD,Core PCE,High,0.3%,0.2%,0.1%,Inflation release
```

## Local storage
The app stores data in:

```text
data/market_analyser.db
```

It keeps:
- economic events
- cached price history
- analysis-related tables for future expansion

## Notes
- The app is designed for local use, not hosting.
- Cached price data is reused automatically when available.
- If a symbol has no data, try a different ticker or date range.
- Calendar interaction is currently focused on browsing and selecting dates; deeper editing can be added later.

## Troubleshooting

### No data appears
- Check the ticker symbol.
- Shorten the date range.
- Make sure you have internet access.

### Streamlit command not found
Use the virtual environment activation steps first, then run the app again.

### PowerShell script blocked
Run:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

## Roadmap
- Better calendar editing actions
- More configurable scoring weights
- Additional data-source options
- Export analysis runs and signals
- More market-type specific validation

## License
No license file has been added yet.
