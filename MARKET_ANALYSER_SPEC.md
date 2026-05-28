# Market Analyser Project Specification

## Purpose
This file defines the project structure, data types, variable names, dependencies, and database format for the Market Analyser app. It is intended to be the single reference for future implementation work so that changing a variable, schema, or database field does not create hidden breakage elsewhere.

## How to Use This File
- Read this file before editing code or data structures.
- Add any new variable, schema field, or child variable here before or at the same time it is introduced in code.
- Update the data type, parent variable, and dependent variables whenever a field changes.
- Keep this file aligned with the implementation, the plan document, and the database schema.

## Project Structure

### Root Level
- `app.py` - Streamlit entry point for the application.
- `requirements.txt` - Python dependency list.
- `README.md` - Run and usage instructions.
- `MARKET_ANALYSER_PLAN.md` - Step-by-step project plan and progress tracker.
- `MARKET_ANALYSER_SPEC.md` - This structure, schema, and variable registry document.

### Python Package
- `src/market_analyser/__init__.py` - Package marker.
- `src/market_analyser/analysis.py` - Data retrieval and market snapshot logic.
- `src/market_analyser/indicators.py` - Technical indicator calculations.
- `src/market_analyser/scoring.py` - Signal scoring and trade level generation.
- `src/market_analyser/interpretation.py` - Indicator meaning and sentiment interpretation.
- `src/market_analyser/ui.py` - Streamlit layout and rendering logic.
- `src/market_analyser/models.py` - Shared typed data models and dataclasses.
- `src/market_analyser/storage.py` - Database read/write helpers.
- `src/market_analyser/config.py` - App constants and default settings.

### Future Optional Folders
- `data/` - Local database or cache files.
- `tests/` - Automated tests.
- `docs/` - Additional design and analysis notes.
- `.streamlit/` - Streamlit configuration if needed later.

## Dependency List

### Runtime Dependencies
| Package | Purpose | Why it is needed |
|---|---|---|
| `streamlit` | UI framework | Renders the analysis page and user inputs |
| `pandas` | Tabular data handling | Stores price history, indicators, and analysis tables |
| `numpy` | Numeric calculations | Supports indicator math and scoring formulas |
| `plotly` | Interactive charts | Used for price charts and sentiment visuals |
| `yfinance` | Market data source | Retrieves stock, index, crypto, and commodity-style data |

### Expected Standard Library Usage
- `dataclasses` for typed records and structured results
- `datetime` for dates and timeframes
- `typing` for `Optional`, `List`, `Dict`, `Literal`, and `Callable`
- `pathlib` for filesystem paths
- `json` for config export and cache metadata
- `sqlite3` for local storage if the database is implemented with SQLite

### Optional Future Dependencies
- `sqlalchemy` if the database layer grows beyond direct SQLite access
- `pydantic` if strict validation becomes necessary
- `pytest` for automated testing

## Core Data Types

### Primitive Types Used
- `str` for symbols, market names, indicator names, and labels
- `int` for counts, periods, and lengths
- `float` for indicator values, prices, scores, and ratios
- `bool` for flags such as enabled/disabled or filtered/unfiltered
- `date` and `datetime` for time boundaries and timestamps
- `None` for missing or unavailable values

### Common Collection Types Used
- `list[str]` for ordered symbol lists or selected indicators
- `dict[str, any]` for dynamic configuration or serialized payloads
- `pandas.DataFrame` for price history and indicator tables
- `tuple` for paired values such as target range or score/value pairing

## Canonical Variable Naming Rules

### Naming Style
- Use `snake_case` for all Python variables.
- Use clear domain-specific names instead of short abbreviations.
- Prefer one meaning per variable.
- Do not reuse a variable name for a different concept in a different function.
- Any new variable must be recorded in the Variable Registry section below.

### Variable Rules
- Input variables should describe the user selection, such as `selected_market_type` or `selected_timeframe`.
- Computed variables should describe the result, such as `indicator_summary` or `predicted_targets`.
- DataFrames should use names that describe their contents, such as `price_history` or `indicator_frame`.
- Boolean flags should start with verbs or state descriptors, such as `show_volume`, `is_valid`, or `has_data`.

## Variable Registry
This registry is the source of truth for named variables and their child variables. When a new variable is added, it should be inserted here with its children and type.

### Root Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `app_state` | `dict[str, any]` | Top-level runtime state for the page | `selected_market_type`, `selected_symbol`, `selected_timeframe`, `selected_indicator_filters`, `analysis_result` |
| `selected_market_type` | `str` | Category selected by the user | `market_group`, `symbol_mapping` |
| `selected_symbol` | `str` | Ticker or instrument symbol | `normalized_symbol`, `provider_symbol` |
| `selected_timeframe` | `str` | Analysis timeframe such as `1d`, `1h`, `15m` | `lookback_window`, `candle_interval` |
| `selected_indicator_filters` | `list[str]` | Filtered indicator names chosen by the user | `visible_indicators` |
| `analysis_result` | `dict[str, any]` | Full result payload shown in the UI | `market_snapshot`, `sentiment_counts`, `ranked_signals`, `indicator_table` |

### Data Fetch Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `raw_price_data` | `pandas.DataFrame` | Price data returned from the provider | `open`, `high`, `low`, `close`, `adj_close`, `volume`, `date` |
| `price_history` | `pandas.DataFrame` | Normalized price data used by analysis | `date`, `open`, `high`, `low`, `close`, `volume` |
| `normalized_symbol` | `str` | Provider-ready symbol name | `provider_symbol` |
| `provider_symbol` | `str` | Symbol passed to the market data API | `provider_format` |

### Indicator Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `indicator_frame` | `pandas.DataFrame` | Price history with indicator columns appended | `sma_20`, `sma_50`, `rsi_14`, `macd`, `macd_signal`, `macd_hist`, `atr_14`, `bb_upper`, `bb_middle`, `bb_lower` |
| `sma_20` | `float` or `pandas.Series` | 20-period moving average | `sma_20_slope` |
| `sma_50` | `float` or `pandas.Series` | 50-period moving average | `sma_50_slope` |
| `rsi_14` | `float` or `pandas.Series` | 14-period relative strength index | `rsi_state` |
| `macd` | `float` or `pandas.Series` | MACD line | `macd_signal`, `macd_hist` |
| `atr_14` | `float` or `pandas.Series` | Average true range | `volatility_band` |
| `bb_upper` | `float` or `pandas.Series` | Upper Bollinger Band | `bb_middle`, `bb_lower` |
| `bb_middle` | `float` or `pandas.Series` | Middle Bollinger Band | `bb_upper`, `bb_lower` |
| `bb_lower` | `float` or `pandas.Series` | Lower Bollinger Band | `bb_middle`, `bb_upper` |

### Interpretation Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `indicator_summary` | `list[dict[str, any]]` | Full indicator interpretation table | `indicator_name`, `indicator_value`, `used_for`, `meaning`, `signal_state`, `priority_order` |
| `indicator_name` | `str` | Display name of the indicator | `indicator_key` |
| `indicator_value` | `float`, `str`, or `None` | Current value to show in the UI | `formatted_value` |
| `used_for` | `str` | Explains what the indicator is used for | `interpretation_text` |
| `meaning` | `str` | Explains what the current value means | `signal_state` |
| `signal_state` | `str` | Sentiment label such as positive, neutral, or negative | `signal_score` |
| `signal_score` | `float` | Numeric confidence assigned to the indicator | `weighted_score` |

### Trade Suggestion Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `ranked_signals` | `list[dict[str, any]]` | Ranked output list sorted by confidence | `target_price`, `stop_loss`, `take_profit`, `prediction_score`, `reasoning` |
| `target_price` | `float` | Predicted target level | `target_range` |
| `stop_loss` | `float` | Risk limit level | `risk_distance` |
| `take_profit` | `float` | Exit profit level | `reward_distance` |
| `prediction_score` | `float` | Overall confidence score | `rank_rank` |

### Summary Variables
| Variable name | Type | Purpose | Child variables |
|---|---|---|---|
| `sentiment_counts` | `dict[str, int]` | Count of positive, neutral, and negative indicators | `positive_count`, `neutral_count`, `negative_count` |
| `positive_count` | `int` | Number of positive indicators | `sentiment_counts` |
| `neutral_count` | `int` | Number of neutral indicators | `sentiment_counts` |
| `negative_count` | `int` | Number of negative indicators | `sentiment_counts` |
| `market_snapshot` | `dict[str, any]` | Top-level market state summary | `latest_close`, `change`, `change_percent`, `average_volume`, `volatility`, `total_return` |

## Database Format

### Recommended Database Type
Use SQLite for the first version because it is local, lightweight, portable, and easy to inspect.

### Database File Format
- Primary database file: `data/market_analyser.db`
- File type: SQLite database
- Encoding: UTF-8 for text columns
- Date storage: ISO 8601 string or SQLite-compatible timestamp
- Numeric storage: `INTEGER` and `REAL`

### Main Database Tables

#### `instruments`
Stores the instruments the user can analyse.

| Column | Type | Purpose |
|---|---|---|
| `instrument_id` | `INTEGER PRIMARY KEY` | Unique identifier |
| `market_type` | `TEXT` | index, stock, metal, oil, crypto |
| `symbol` | `TEXT` | Original symbol entered by user |
| `normalized_symbol` | `TEXT` | Symbol after provider normalization |
| `display_name` | `TEXT` | Human-friendly label |
| `is_active` | `INTEGER` | Active/inactive flag |
| `created_at` | `TEXT` | Record creation time |

#### `analysis_runs`
Stores one analysis execution per user request.

| Column | Type | Purpose |
|---|---|---|
| `run_id` | `INTEGER PRIMARY KEY` | Unique run identifier |
| `instrument_id` | `INTEGER` | Foreign key to `instruments` |
| `timeframe` | `TEXT` | Selected timeframe |
| `start_date` | `TEXT` | Start of requested analysis range |
| `end_date` | `TEXT` | End of requested analysis range |
| `overall_score` | `REAL` | Combined confidence score |
| `sentiment_state` | `TEXT` | Overall market direction |
| `created_at` | `TEXT` | Timestamp for the run |

#### `indicator_results`
Stores the per-indicator output for each run.

| Column | Type | Purpose |
|---|---|---|
| `indicator_result_id` | `INTEGER PRIMARY KEY` | Unique result identifier |
| `run_id` | `INTEGER` | Foreign key to `analysis_runs` |
| `indicator_key` | `TEXT` | Internal name of the indicator |
| `indicator_name` | `TEXT` | Display name |
| `indicator_value` | `REAL` or `TEXT` | Computed value |
| `signal_state` | `TEXT` | positive, neutral, or negative |
| `used_for` | `TEXT` | Purpose description |
| `meaning` | `TEXT` | Interpretation of the value |
| `weight` | `REAL` | Relative importance in scoring |
| `created_at` | `TEXT` | Timestamp |

#### `trade_signals`
Stores ranked target, stop loss, and take profit suggestions.

| Column | Type | Purpose |
|---|---|---|
| `trade_signal_id` | `INTEGER PRIMARY KEY` | Unique trade signal identifier |
| `run_id` | `INTEGER` | Foreign key to `analysis_runs` |
| `target_price` | `REAL` | Suggested target |
| `stop_loss` | `REAL` | Suggested stop loss |
| `take_profit` | `REAL` | Suggested take profit |
| `prediction_score` | `REAL` | Confidence score |
| `rank_order` | `INTEGER` | Sort order |
| `reasoning` | `TEXT` | Explanation for the score |
| `created_at` | `TEXT` | Timestamp |

### Sub Database Format
If the app needs logical sub-databases, keep them as separate SQLite files or separate table groups inside the main database.

#### Recommended Sub Database Files
- `data/cache.db` - temporary cache for downloaded market data
- `data/analysis.db` - persistent analysis history and signal outputs
- `data/config.db` - saved user preferences and app defaults

### Sub Database Purpose

#### `cache.db`
Used for temporary market data storage.

Suggested tables:
- `price_cache`
- `provider_metadata`

#### `analysis.db`
Used for historic analysis and results.

Suggested tables:
- `analysis_runs`
- `indicator_results`
- `trade_signals`

#### `config.db`
Used for user preferences and application settings.

Suggested tables:
- `ui_preferences`
- `default_watchlist`
- `analysis_settings`

### Database Relationship Rules
- Each analysis run belongs to one instrument.
- Each run can have many indicator results.
- Each run can have many trade signals.
- Each indicator result must reference one indicator key.
- Cache tables should not be used as the source of truth for final analysis.

## File-Level Variable Tracking Rule
Whenever a new variable is introduced in code, add it to the relevant section in this file with:
- variable name
- data type
- purpose
- parent variable
- child variables
- related tables or fields

This rule applies to:
- Python variables
- Dataclass fields
- DataFrame columns
- Database columns
- UI state variables
- Derived metrics

## Update Workflow
When modifying the app:
1. Update this specification first or alongside the code.
2. Update the implementation.
3. Verify the variable names and data types still match.
4. Record any unresolved behavior in the analysis log in `MARKET_ANALYSER_PLAN.md`.

## Progress Tracker
- [x] Detailed project structure documented
- [x] Dependency list documented
- [x] Variable registry created
- [x] Database and sub-database format documented
- [ ] Code implementation fully aligned with this spec
- [ ] Automated validation added

## Change Log
- 2026-05-28: Created the initial project specification file with structure, dependencies, variable registry, and database design.
