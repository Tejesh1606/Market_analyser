from __future__ import annotations

import calendar
from numbers import Number
from datetime import date, timedelta, datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from .economic_events import import_events_from_csv_text, get_recent_events, to_dataframe
from .storage import init_db, save_trade_signal
from .ml import predict_for_latest, train_model, load_trained_model, meta_path_for_interval
from .live_quotes import fetch_xau_api_quote


def _shift_month(anchor_date: date, delta_months: int) -> date:
    month_index = anchor_date.month - 1 + delta_months
    year = anchor_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(anchor_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _prepare_event_frame(events) -> pd.DataFrame:
    df = to_dataframe(events)
    if df.empty:
        return df

    df = df.copy()
    df["event_time_dt"] = pd.to_datetime(df.get("event_time"), errors="coerce")
    df["event_day"] = df["event_time_dt"].dt.date
    df["event_clock"] = df["event_time_dt"].dt.strftime("%H:%M").fillna("")
    df["impact"] = df.get("impact", "Unknown").fillna("Unknown")
    return df.sort_values(by=["event_time_dt", "event_name"], ascending=[False, True], na_position="last")


def _impact_class(impact: str) -> str:
    normalized = str(impact or "").strip().lower()
    if normalized == "high":
        return "high"
    if normalized == "medium":
        return "medium"
    if normalized == "low":
        return "low"
    if normalized == "holiday":
        return "holiday"
    return "unknown"


def _render_calendar_styles() -> None:
    st.markdown(
        """
        <style>
        .ma-cal-wrap { border: 1px solid rgba(128,128,128,0.2); border-radius: 14px; padding: 0.75rem; background: rgba(255,255,255,0.02); }
        .ma-cal-title { font-size: 1.15rem; font-weight: 700; margin: 0; }
        .ma-cal-subtitle { color: rgba(255,255,255,0.65); font-size: 0.85rem; margin-top: 0.15rem; }
        .ma-cal-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 0.4rem; }
        .ma-cal-dow { font-size: 0.72rem; font-weight: 700; opacity: 0.75; text-transform: uppercase; padding: 0 0.35rem; }
        .ma-cal-cell { min-height: 108px; border-radius: 14px; padding: 0.4rem; background: rgba(255,255,255,0.02); }
        .ma-cal-cell--empty { background: transparent; }
        .ma-cal-cell--today { box-shadow: inset 0 0 0 1px rgba(50,140,255,0.25); }
        .ma-cal-cell--selected { box-shadow: inset 0 0 0 1px rgba(0,170,120,0.35); }
        .ma-cal-daynum { display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 0.92rem; margin-bottom: 0.3rem; }
        .ma-cal-badge { font-size: 0.68rem; padding: 0.08rem 0.38rem; border-radius: 999px; background: rgba(255,255,255,0.12); }
        .ma-cal-event { border-radius: 8px; padding: 0.18rem 0.35rem; margin-top: 0.18rem; font-size: 0.7rem; line-height: 1.15; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .ma-cal-event.high { background: rgba(220, 53, 69, 0.18); color: #ffb4bd; }
        .ma-cal-event.medium { background: rgba(255, 193, 7, 0.18); color: #ffe59e; }
        .ma-cal-event.low { background: rgba(13, 110, 253, 0.18); color: #b9d4ff; }
        .ma-cal-event.holiday { background: rgba(111, 66, 193, 0.18); color: #d3c0ff; }
        .ma-cal-event.unknown { background: rgba(160, 160, 160, 0.18); color: #e2e2e2; }
        .ma-cal-agenda { border-left: 3px solid rgba(128,128,128,0.22); padding-left: 0.75rem; }
        .ma-cal-agenda-item { padding: 0.55rem 0.7rem; border-radius: 10px; border: 1px solid rgba(128,128,128,0.14); margin-bottom: 0.45rem; }
        .ma-cal-agenda-top { display: flex; justify-content: space-between; gap: 0.5rem; font-weight: 700; font-size: 0.85rem; }
        .ma-cal-agenda-meta { opacity: 0.75; font-size: 0.78rem; margin-top: 0.15rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_price_chart(history, show_volume: bool = True) -> None:
    if history is None or history.empty:
        st.warning("No price history to plot.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history["Date"], y=history["Close"], name="Close", line=dict(width=2)))

    if "BB_UPPER" in history.columns and "BB_LOWER" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["BB_UPPER"], name="BB Upper", line=dict(width=1), marker=dict(opacity=0.4)))
        fig.add_trace(go.Scatter(x=history["Date"], y=history["BB_LOWER"], name="BB Lower", line=dict(width=1), marker=dict(opacity=0.4), fill="tonexty", fillcolor="rgba(200,200,255,0.1)"))
    if "BB_MIDDLE" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["BB_MIDDLE"], name="BB Middle", line=dict(width=1, dash="dot")))

    if "SMA_20" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["SMA_20"], name="SMA 20", line=dict(width=1.2, dash="dot")))
    if "SMA_50" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["SMA_50"], name="SMA 50", line=dict(width=1.2, dash="dash")))

    fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    if show_volume and "Volume" in history.columns:
        vfig = go.Figure()
        vfig.add_trace(go.Bar(x=history["Date"], y=history["Volume"], name="Volume"))
        vfig.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(vfig, use_container_width=True)


def render_indicator_chart(history) -> None:
    if history is None or history.empty:
        st.warning("No indicator data to plot.")
        return

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("MACD", "RSI", "Stochastic", "Bulls / Bears Power"),
    )

    if "MACD_HIST" in history.columns:
        fig.add_trace(go.Bar(x=history["Date"], y=history["MACD_HIST"], name="MACD Hist", marker_color="grey"), row=1, col=1)
    if "MACD" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["MACD"], name="MACD", line=dict(color="blue")), row=1, col=1)
    if "MACD_SIGNAL" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["MACD_SIGNAL"], name="Signal", line=dict(color="red", dash="dot")), row=1, col=1)

    if "RSI_14" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["RSI_14"], name="RSI 14", line=dict(color="purple")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="lightgrey", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="lightgrey", row=2, col=1)

    if "STOCH_K" in history.columns and "STOCH_D" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["STOCH_K"], name="%K", line=dict(color="green")), row=3, col=1)
        fig.add_trace(go.Scatter(x=history["Date"], y=history["STOCH_D"], name="%D", line=dict(color="orange", dash="dot")), row=3, col=1)
        fig.add_hline(y=80, line_dash="dash", line_color="lightgrey", row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="lightgrey", row=3, col=1)

    if "BULLS_POWER" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["BULLS_POWER"], name="Bulls Power", line=dict(color="teal")), row=4, col=1)
    if "BEARS_POWER" in history.columns:
        fig.add_trace(go.Scatter(x=history["Date"], y=history["BEARS_POWER"], name="Bears Power", line=dict(color="maroon")), row=4, col=1)

    fig.update_layout(height=980, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)


def _render_economic_events_panel() -> None:
    st.subheader("Economic calendar / events")
    st.caption("Calendar-style view with local event entry, plus paste/upload for bulk imports.")

    _render_calendar_styles()

    events = get_recent_events(limit=200)
    df = _prepare_event_frame(events)

    if "economic_calendar_focus" not in st.session_state:
        st.session_state["economic_calendar_focus"] = date.today()
    if "economic_calendar_selected_date" not in st.session_state:
        st.session_state["economic_calendar_selected_date"] = st.session_state["economic_calendar_focus"]

    focus_date = st.date_input("Focus date", value=st.session_state["economic_calendar_focus"], key="economic_calendar_focus_picker")
    st.session_state["economic_calendar_focus"] = focus_date
    st.session_state["economic_calendar_selected_date"] = focus_date

    nav_left, nav_mid, nav_right = st.columns([1, 3, 1])
    with nav_left:
        if st.button("◀ Prev", use_container_width=True):
            st.session_state["economic_calendar_focus"] = _shift_month(focus_date, -1)
            st.session_state["economic_calendar_selected_date"] = st.session_state["economic_calendar_focus"]
            st.rerun()
    with nav_mid:
        st.markdown(f"<div class='ma-cal-wrap'><div class='ma-cal-title'>{focus_date.strftime('%B %Y')}</div><div class='ma-cal-subtitle'>Google-calendar style overview with events and agenda</div></div>", unsafe_allow_html=True)
    with nav_right:
        if st.button("Next ▶", use_container_width=True):
            st.session_state["economic_calendar_focus"] = _shift_month(focus_date, 1)
            st.session_state["economic_calendar_selected_date"] = st.session_state["economic_calendar_focus"]
            st.rerun()

    month_weeks = calendar.monthcalendar(focus_date.year, focus_date.month)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today = date.today()

    events_by_day: dict[date, pd.DataFrame] = {}
    if not df.empty:
        for event_day, group in df.dropna(subset=["event_day"]).groupby("event_day"):
            events_by_day[event_day] = group

    st.markdown("<div class='ma-cal-grid'>" + "".join(f"<div class='ma-cal-dow'>{day}</div>" for day in weekdays) + "</div>", unsafe_allow_html=True)

    for week in month_weeks:
        cols = st.columns(7)
        for idx, day_num in enumerate(week):
            with cols[idx]:
                if day_num == 0:
                    with st.container(border=False):
                        st.markdown("<div class='ma-cal-cell ma-cal-cell--empty'></div>", unsafe_allow_html=True)
                    continue

                cell_date = date(focus_date.year, focus_date.month, day_num)
                event_group = events_by_day.get(cell_date)
                cell_classes = ["ma-cal-cell"]
                if cell_date == today:
                    cell_classes.append("ma-cal-cell--today")
                if cell_date == st.session_state["economic_calendar_selected_date"]:
                    cell_classes.append("ma-cal-cell--selected")

                badge = f"<span class='ma-cal-badge'>{len(event_group)} event(s)</span>" if event_group is not None else ""
                preview = ""
                if event_group is not None:
                    preview_lines = []
                    for _, event_row in event_group.head(3).iterrows():
                        impact_class = _impact_class(event_row.get("impact"))
                        time_text = event_row.get("event_clock") or "--:--"
                        name_text = str(event_row.get("event_name") or "Unnamed event")
                        preview_lines.append(f"<div class='ma-cal-event {impact_class}'>{time_text} · {name_text}</div>")
                    if len(event_group) > 3:
                        preview_lines.append(f"<div class='ma-cal-event unknown'>+{len(event_group) - 3} more</div>")
                    preview = "".join(preview_lines)

                with st.container(border=True):
                    day_label_col, day_badge_col = st.columns([0.8, 1.2])
                    with day_label_col:
                        if st.button(str(day_num), key=f"economic_day_{cell_date.isoformat()}", use_container_width=True):
                            st.session_state["economic_calendar_selected_date"] = cell_date
                            st.session_state["economic_calendar_focus"] = cell_date
                            st.rerun()
                    with day_badge_col:
                        st.markdown(f"<div class='ma-cal-daynum'>{badge}</div>", unsafe_allow_html=True)
                    if preview:
                        st.markdown(preview, unsafe_allow_html=True)

    agenda_events = pd.DataFrame()
    if not df.empty:
        agenda_events = df[df["event_day"] == st.session_state["economic_calendar_selected_date"]].copy()

    left_agenda, right_agenda = st.columns([1.15, 0.85])
    with left_agenda:
        st.markdown("<div class='ma-cal-agenda'>", unsafe_allow_html=True)
        selected_date = st.session_state["economic_calendar_selected_date"]
        st.markdown(f"**Agenda for {selected_date.strftime('%A, %d %B %Y')}**")
        if agenda_events.empty:
            st.info("No events stored for this date.")
        else:
            for _, event_row in agenda_events.iterrows():
                st.markdown(
                    f"""
                    <div class='ma-cal-agenda-item'>
                        <div class='ma-cal-agenda-top'><span>{event_row.get('event_clock') or '--:--'} · {event_row.get('event_name') or 'Unnamed event'}</span><span class='ma-cal-badge'>{event_row.get('impact') or 'Unknown'}</span></div>
                        <div class='ma-cal-agenda-meta'>{event_row.get('currency') or ''} · {event_row.get('source') or 'manual'} · {event_row.get('notes') or ''}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_agenda:
        if df.empty:
            st.metric("Stored events", 0)
        else:
            st.metric("Stored events", int(len(df)))
            st.metric("High impact", int((df["impact"].astype(str).str.lower() == "high").sum()))

    with st.expander("Add event", expanded=True):
        with st.form("economic_event_form", clear_on_submit=True):
            event_date = st.date_input("Event date", value=date.today())
            event_time = st.time_input("Event time")
            event_name = st.text_input("Event name", placeholder="CPI, FOMC, NFP, GDP...")
            currency = st.text_input("Currency / country", placeholder="USD, EUR, GBP, US")
            impact = st.selectbox("Impact", ["Low", "Medium", "High", "Holiday", "Unknown"])
            actual = st.text_input("Actual", placeholder="e.g. 0.3%")
            forecast = st.text_input("Forecast", placeholder="e.g. 0.2%")
            previous = st.text_input("Previous", placeholder="e.g. 0.1%")
            notes = st.text_area("Notes", placeholder="Why this event matters for the selected market")
            submit = st.form_submit_button("Save event locally")

        if submit:
            event_dt = datetime.combine(event_date, event_time)
            from .storage import save_economic_events

            rows = [
                {
                    "event_time": event_dt.isoformat(sep=" ", timespec="minutes"),
                    "currency": currency.strip().upper(),
                    "event_name": event_name.strip(),
                    "impact": impact,
                    "actual": actual.strip(),
                    "forecast": forecast.strip(),
                    "previous": previous.strip(),
                    "notes": notes.strip(),
                    "source": "calendar",
                }
            ]
            written = save_economic_events(rows)
            st.success(f"Saved {written} event(s) locally.")

    with st.expander("Paste economic data", expanded=False):
        csv_text = st.text_area(
            "Paste CSV here",
            height=180,
            placeholder="event_time,currency,event_name,impact,actual,forecast,previous,notes\n2026-05-28 13:30,USD,Core PCE High,High,0.3%,0.2%,0.1%,Inflation release",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Save pasted events"):
                count = import_events_from_csv_text(csv_text)
                st.success(f"Saved {count} event(s) locally.")
        with col_b:
            uploaded = st.file_uploader("Or upload CSV", type=["csv"], label_visibility="collapsed")
            if uploaded is not None and st.button("Import uploaded CSV"):
                text = uploaded.read().decode("utf-8", errors="ignore")
                count = import_events_from_csv_text(text)
                st.success(f"Imported {count} event(s) from file.")

    with st.expander("Show raw table", expanded=False):
        if df.empty:
            st.info("No local events stored yet.")
        else:
            raw_df = df.drop(columns=["event_time_dt", "event_day", "event_clock"], errors="ignore")
            st.dataframe(raw_df, use_container_width=True, height=260)


def render_dashboard(*, run_button_label: str = "Run analysis") -> None:
    init_db()
    st.title("Market Analyser")
    st.caption("Explore price action, indicators, trade suggestions, and economic events.")

    with st.sidebar:
        st.header("Controls")
        symbol = st.text_input("Symbol", value="AAPL").strip().upper() or "AAPL"
        provider = st.selectbox("Provider", ["auto", "alpha_vantage", "yfinance"], index=0)
        end_date = st.date_input("End date", value=date.today())
        start_date = st.date_input("Start date", value=end_date - timedelta(days=365))
        interval = st.selectbox("Interval", ["1d", "60m", "15m", "5m", "1m"], index=0)
        bypass_cache = st.checkbox("Bypass cache / Force download", value=False, help="Force a fresh download and ignore cached data for this run")
        show_volume = st.checkbox("Show volume", value=True)
        save_prediction = st.checkbox("Save ML prediction", value=True, help="Store the latest predicted target/SL/TP in the local DB")
        live_price_check = st.checkbox("Check live quote (XAU-API)", value=True, help="Compare the latest candle against a live price from XAU-API when available")
        run = st.button(run_button_label)

        st.divider()
        st.subheader("ML model")
        model_loaded = load_trained_model(interval=interval)
        model_meta_path = meta_path_for_interval(interval)
        if model_loaded and model_meta_path.exists():
            try:
                meta = pd.read_json(model_meta_path, typ="series")
                st.caption(f"Trained horizon: {meta.get('horizon', 'n/a')} bars")
                scores = meta.get("scores", {})
                if isinstance(scores, dict):
                    r2 = scores.get("r2")
                    mae = scores.get("mae")
                    if isinstance(r2, Number) and isinstance(mae, Number):
                        st.caption(f"R²: {float(r2):.3f} | MAE: {float(mae):.4f}")
                    else:
                        st.caption("Model ready")
            except Exception:
                st.caption("Model ready")
        else:
            st.caption("No trained model saved yet")

        with st.expander("Train / retrain model", expanded=False):
            train_horizon = st.number_input("Prediction horizon (bars)", min_value=1, max_value=20, value=5, step=1)
            train_estimators = st.number_input("Trees (n_estimators)", min_value=10, max_value=300, value=50, step=10)
            train_button = st.button("Train model now", use_container_width=True)
            if train_button:
                with st.spinner("Training model from cached history..."):
                    try:
                        result = train_model(horizon=int(train_horizon), n_estimators=int(train_estimators), interval=interval)
                        st.success("Model trained and saved locally.")
                        st.write(result)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Training failed: {exc}")

        st.divider()
        st.subheader("Economic events")
        st.caption("Paste or upload CSV to save local calendar data.")

    if start_date >= end_date:
        st.error("Start date must be earlier than end date.")
        return

    if not run:
        st.write("Select inputs and press Run analysis")
        _render_economic_events_panel()
        return

    try:
        from .analysis import fetch_price_history, build_market_snapshot
        from .indicators import calculate_indicators
        from .interpretation import interpret_indicators
        from .scoring import generate_trade_signals
    except Exception as e:
        st.error(f"Required analysis modules missing: {e}")
        _render_economic_events_panel()
        return

    with st.spinner(f"Loading {symbol}..."):
        history = fetch_price_history(symbol, start_date, end_date, interval=interval, force_refresh=bypass_cache, provider=provider)

    if history is None or history.empty:
        st.warning("No data found for that symbol and date range.")
        _render_economic_events_panel()
        return

    indicator_frame = calculate_indicators(history)
    interpretations = interpret_indicators(indicator_frame)
    signals = generate_trade_signals(symbol, history, indicator_frame, max_signals=3)

    live_quote = None
    live_quote_delta = None
    if live_price_check:
        live_quote = fetch_xau_api_quote(symbol)
        if live_quote is not None:
            live_quote_delta = live_quote - float(indicator_frame["Close"].dropna().iloc[-1])

    ml_prediction = None
    try:
        ml_prediction = predict_for_latest(symbol, interval=interval)
    except Exception:
        ml_prediction = None

    if ml_prediction:
        pred_target = float(ml_prediction.get("pred_tp") or 0)
        pred_sl = float(ml_prediction.get("pred_sl") or 0)
        pred_ret = float(ml_prediction.get("pred_ret") or 0)
        st.info(
            f"ML prediction: target {pred_target:,.2f}, stop loss {pred_sl:,.2f}, expected return {pred_ret:+.2%}"
        )
        if save_prediction:
            try:
                save_trade_signal(
                    target_price=pred_target,
                    stop_loss=pred_sl,
                    take_profit=pred_target,
                    prediction_score=pred_ret,
                    reasoning=f"ML prediction for {symbol}",
                )
            except Exception:
                pass

    try:
        snapshot = build_market_snapshot(symbol, indicator_frame)
    except Exception:
        snapshot = None

    left_col, right_col = st.columns([2.2, 1.0])

    with left_col:
        if snapshot:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Latest close", f"${snapshot.get('latest_close', 0):,.2f}")
            c2.metric("Change", f"{snapshot.get('change', 0):+.2f}")
            c3.metric("Change %", f"{snapshot.get('change_percent', 0):+.2f}%")
            c4.metric("Volatility", f"{snapshot.get('volatility', 0):.2f}%")

        if live_quote is not None:
            live_cols = st.columns(2)
            live_cols[0].metric("Live quote", f"${live_quote:,.2f}")
            if live_quote_delta is not None:
                live_cols[1].metric("Live vs latest candle", f"{live_quote_delta:+,.2f}")
            st.caption("Live quote source: XAU-API current price endpoint")
        elif live_price_check:
            st.info("Live quote check was enabled, but the XAU-API service did not return a price. Set `XAU_API_BASE_URL` and `XAU_API_KEY` if needed.")

        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for it in interpretations:
            state = it.get("signal_state", "neutral")
            sentiment_counts[state] = sentiment_counts.get(state, 0) + 1

        gauge_fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=sentiment_counts.get("positive", 0),
                title={"text": "Positive indicator count"},
                gauge={
                    "axis": {"range": [0, max(1, len(interpretations))]},
                    "bar": {"color": "green"},
                    "steps": [
                        {"range": [0, sentiment_counts.get("negative", 0)], "color": "rgba(255,0,0,0.15)"},
                        {"range": [sentiment_counts.get("negative", 0), sentiment_counts.get("negative", 0) + sentiment_counts.get("neutral", 0)], "color": "rgba(200,200,200,0.2)"},
                        {"range": [sentiment_counts.get("negative", 0) + sentiment_counts.get("neutral", 0), max(1, len(interpretations))], "color": "rgba(0,128,0,0.15)"},
                    ],
                },
            )
        )
        gauge_fig.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(gauge_fig, use_container_width=True)

        st.subheader("Ranked trade suggestions")
        if signals:
            signal_df = pd.DataFrame(signals)
            st.dataframe(signal_df, use_container_width=True, height=220)
        else:
            st.info("No signals available.")

        st.subheader("Indicator analysis")
        if interpretations:
            filter_options = [x["indicator_key"] for x in interpretations]
            selected = st.multiselect("Filter indicators", filter_options, default=filter_options)
            filtered = [x for x in interpretations if x["indicator_key"] in selected]
            st.dataframe(pd.DataFrame(filtered), use_container_width=True, height=320)
        else:
            st.info("No indicator interpretations available.")

        st.subheader("Price and indicator charts")
        render_price_chart(indicator_frame, show_volume=show_volume)
        render_indicator_chart(indicator_frame)

    with right_col:
        _render_economic_events_panel()

        st.subheader("Result summary")
        st.write({
            "positive": sentiment_counts.get("positive", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "negative": sentiment_counts.get("negative", 0),
            "total_indicators": len(interpretations),
        })
