# Market Analyser Project Plan

## Purpose
Build a market analysis app that lets the user select an instrument such as an index, stock, metal, oil, or crypto asset, choose a timeframe, and receive a structured analysis containing:

- Market direction summary
- Indicator-by-indicator interpretation
- Positive / neutral / negative indicator count
- Ranked target, stop loss, and take profit suggestions
- A filterable indicator table
- A progress log that can be reviewed later

This document is intended to stay with the project so future work can be analysed in detail.

## How to Use This Document
- Read the current status before starting any new work.
- Update the progress tracker after every meaningful implementation step.
- Add notes to the analysis log when a design decision, issue, or tradeoff matters.
- Keep the plan aligned with the actual codebase; remove or revise steps when the implementation changes.
- Use [MARKET_ANALYSER_SPEC.md](MARKET_ANALYSER_SPEC.md) as the source of truth for project structure, variable names, data types, dependencies, and database format.

## Project Scope

### In Scope
- Market selection for index, stock, metal, oil, and crypto
- Timeframe selection for analysis
- Indicator calculation and interpretation layer
- Sentiment classification for each indicator
- Target / stop loss / take profit estimation
- Semi-circle style sentiment summary chart
- Filterable indicator table with explanation columns
- Ranked signals sorted by predicted score
- Reusable backend logic for future expansion

### Out of Scope for the First Version
- Real-time trading execution
- Brokerage integration
- Auto-order placement
- Machine learning model training pipeline
- News sentiment ingestion
- Alerts and notifications

## Detailed Implementation Plan

### Phase 1: Define the Instrument Model
Goal: make sure the app understands which market type the user selected and which symbol format to use.

Steps:
1. Define supported market categories.
2. Create a symbol mapping strategy for each category.
3. Add validation for unsupported or empty symbols.
4. Decide how each market type maps to the data provider.
5. Document special cases such as commodities and crypto.

Deliverables:
- Market type enum or equivalent structure
- Symbol normalization helper
- Validation rules

Progress check:
- [ ] Market types defined
- [ ] Symbol mapping logic defined
- [ ] Unsupported symbol handling documented

### Phase 2: Define Analysis Inputs
Goal: collect all inputs needed to evaluate the selected market.

Steps:
1. Add market type input.
2. Add symbol input.
3. Add timeframe input.
4. Add optional date-range input if needed.
5. Define default values for first-time usage.
6. Confirm the data window needed by the indicators.

Deliverables:
- Input schema
- Default configuration
- Validation messages

Progress check:
- [ ] Instrument input exists
- [ ] Timeframe input exists
- [ ] Validation behavior defined

### Phase 3: Build the Data Fetch Layer
Goal: retrieve market price data in a reusable and consistent way.

Steps:
1. Choose the market data source.
2. Implement one fetch function for all asset types where possible.
3. Handle missing data, empty responses, and provider failures.
4. Normalize column names to a common format.
5. Ensure the data window supports all selected indicators.

Deliverables:
- Shared data fetch service
- Normalized price history structure
- Error handling for bad data

Progress check:
- [ ] Data fetch function exists
- [ ] Error handling exists
- [ ] Data normalization exists

### Phase 4: Build the Indicator Engine
Goal: calculate all indicators that the analysis screen will display.

Steps:
1. Choose the first release indicator set.
2. Group indicators by type such as trend, momentum, volatility, and volume.
3. Implement calculations in reusable functions.
4. Make sure each indicator returns a consistent output.
5. Ensure the calculation layer supports the selected timeframe.
6. Keep the indicator output independent from UI formatting.

Suggested first-release indicators:
- Moving averages
- RSI
- MACD
- Bollinger Bands
- ATR
- Volume moving average
- Trend strength or slope
- Support / resistance approximation

Deliverables:
- Indicator calculation module
- Structured indicator output
- Timeframe-aware calculations

Progress check:
- [ ] Core indicators selected
- [ ] Indicator calculation module exists
- [ ] Output structure standardized

### Phase 5: Build the Indicator Interpretation Layer
Goal: explain what each indicator means for the selected market.

Steps:
1. Define a positive / neutral / negative rule for each indicator.
2. Add plain-language interpretation text for every indicator.
3. Add a "used for" description beside the value.
4. Add a "what it means" column for the current reading.
5. Keep interpretation rules easy to adjust later.
6. Make sure every indicator can be reviewed on its own.

Deliverables:
- Indicator interpretation rules
- Human-readable explanation text
- Sentiment classification for each indicator

Progress check:
- [ ] Every indicator has an explanation
- [ ] Every indicator has a sentiment label
- [ ] Interpretation rules documented

### Phase 6: Build the Signal Scoring System
Goal: convert indicator signals into ranked target, stop loss, and take profit suggestions.

Steps:
1. Define how indicator sentiment contributes to a score.
2. Assign weights to indicators by importance.
3. Separate trend logic from risk logic.
4. Derive a candidate target, stop loss, and take profit level.
5. Produce a prediction score for each suggestion.
6. Sort signals by score so the strongest appears first.
7. Make the scoring rules easy to tune later.

Deliverables:
- Signal scoring function
- Ranked output list
- Target / SL / TP suggestion logic

Progress check:
- [ ] Scoring formula exists
- [ ] Ranked signals exist
- [ ] Target / SL / TP generation exists

### Phase 7: Build the Sentiment Summary Visual
Goal: show how many indicators are positive, neutral, and negative.

Steps:
1. Count the indicator classifications.
2. Select a semi-circle or gauge-style visualization.
3. Place the summary at the top of the analysis page.
4. Make the display easy to read at a glance.
5. Ensure the chart updates when the indicator filter changes.

Deliverables:
- Sentiment count summary
- Semi-circle style visual
- Dynamic refresh behavior

Progress check:
- [ ] Sentiment counts calculated
- [ ] Visual added
- [ ] Visual refreshes with filter changes

### Phase 8: Build the Analysis Results Layout
Goal: arrange the results in a clear hierarchy.

Steps:
1. Put market summary at the top.
2. Put sentiment chart below the summary.
3. Place ranked trade ideas next.
4. Place the indicator table below the ranking section.
5. Keep the layout readable on smaller screens.
6. Add tabs or sections only if they improve clarity.

Deliverables:
- Final results layout
- Clear ordering of sections
- Responsive presentation

Progress check:
- [ ] Layout order defined
- [ ] Mobile-friendly presentation considered
- [ ] Results hierarchy established

### Phase 9: Build the Indicator Table
Goal: show all indicators in a detailed table that can be analysed later.

Steps:
1. Add columns for indicator name, value, use, and meaning.
2. Add a sentiment column.
3. Add a filter panel for indicator selection.
4. Refresh the page or table after filter changes.
5. Keep the table ordered by the chosen analysis sequence.
6. Support future export or download features if needed.

Deliverables:
- Filterable indicator table
- Column definitions
- Stable sort order

Progress check:
- [ ] Table columns defined
- [ ] Filter behavior exists
- [ ] Filtered reload behavior exists

### Phase 10: Build the UI Controls
Goal: make the app easy to use without hiding the analysis logic.

Steps:
1. Add instrument selection controls.
2. Add timeframe controls.
3. Add indicator filter controls.
4. Add analysis trigger or automatic refresh behavior.
5. Show loading and error states clearly.
6. Make default settings useful for first-time users.

Deliverables:
- Sidebar or control panel
- Friendly defaults
- Clear loading/error states

Progress check:
- [ ] Instrument selector exists
- [ ] Timeframe selector exists
- [ ] Filter controls exist

### Phase 11: Add Validation and Edge Case Handling
Goal: keep the app reliable when data is incomplete or the user input is invalid.

Steps:
1. Handle empty data responses.
2. Handle unsupported symbols.
3. Handle missing indicator values.
4. Handle very short history windows.
5. Handle sudden provider failures gracefully.
6. Show useful messages instead of silent failure.

Deliverables:
- Validation layer
- Error messages
- Graceful fallback handling

Progress check:
- [ ] Empty data handled
- [ ] Invalid input handled
- [ ] Provider failure handled

### Phase 12: Testing and Review
Goal: make sure the result is correct enough to trust for analysis.

Steps:
1. Test at least one symbol from each market type.
2. Test multiple timeframes.
3. Verify indicator counts and labels.
4. Verify the ranking order is stable.
5. Verify filters change the visible indicators correctly.
6. Review whether target, SL, and TP look sensible.
7. Record bugs and tuning needs in the analysis log.

Deliverables:
- Manual test checklist
- Review notes
- Bug and tuning list

Progress check:
- [ ] Market types tested
- [ ] Timeframes tested
- [ ] Filters tested
- [ ] Ranking tested

## Progress Tracker

Update this section as work moves forward.

| Step | Status | Notes |
|---|---|---|
| Instrument model | Not started |  |
| Analysis inputs | Not started |  |
| Data fetch layer | Not started |  |
| Indicator engine | Not started |  |
| Interpretation layer | Not started |  |
| Signal scoring | Not started |  |
| Sentiment visual | Not started |  |
| Results layout | Not started |  |
| Indicator table | Not started |  |
| UI controls | Not started |  |
| Validation and edge cases | Not started |  |
| Testing and review | Not started |  |

## Analysis Log
Use this area to capture detailed decisions and later review why something was built a certain way.

### Entry Template
- Date:
- Area:
- Decision:
- Reasoning:
- Alternatives considered:
- Follow-up needed:

### Notes
- Keep entries short but specific.
- Record changes that affect indicator logic, scoring, or user interpretation.
- Add one entry per meaningful design decision or bug fix.

## Suggested Future Enhancements
- Watchlist support
- Saved analysis history
- Export to CSV or PDF
- Alerting when indicator sentiment changes
- Backtesting mode
- Compare multiple instruments side by side

## Maintenance Rule
When the project changes, update this file in the same session if possible so the documentation stays in sync with the implementation.
