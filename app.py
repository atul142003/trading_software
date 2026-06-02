import streamlit as st
import pandas as pd
import yfinance as yf

from indicators.technical import add_indicators
from ai.trend import detect_trend
from ai.signals import generate_signal
from ai.predict import predict_direction
from ai.multi_timeframe import analyze_timeframe
from patterns.candles import detect_pattern
from ai.explain import explain_signal

st.set_page_config(
    page_title="AI Trading Software V1.1",
    layout="wide"
)

st.title("📈 AI Trading Software V1.1")

symbol = st.text_input(
    "Enter Symbol",
    "RELIANCE.NS"
)

if st.button("Analyze"):

    # Download Daily Data
    df = yf.download(
        symbol,
        period="2y",
        interval="1d",
        progress=False
    )

    if len(df) == 0:
        st.error("No data found.")
        st.stop()

    # Fix Yahoo MultiIndex issue
    if hasattr(df.columns, "levels"):
        df.columns = [c[0] for c in df.columns]

    # Add Indicators
    df = add_indicators(df)

    latest = df.iloc[-1]
    reasons = explain_signal(latest)

    # Core Analysis
    trend = detect_trend(latest)

    signal = generate_signal(latest)

    pattern = detect_pattern(df)

    # AI Prediction
    features = [
        latest["RSI"],
        latest["EMA20"],
        latest["EMA50"],
        latest["MACD"]
    ]

    prediction, confidence = predict_direction(features)

    # =========================
    # MAIN ANALYSIS
    # =========================

    st.subheader("Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Trend", trend)

    with col2:
        st.metric("Signal", signal)

    with col3:
        st.metric("Pattern", pattern)

    st.metric(
        "AI Prediction",
        f"{prediction} ({confidence}%)"
    )

    # =========================
    # INDICATORS
    # =========================

    st.subheader("Technical Indicators")

    indicator_data = {
        "RSI": round(latest["RSI"], 2),
        "MACD": round(latest["MACD"], 2),
        "EMA20": round(latest["EMA20"], 2),
        "EMA50": round(latest["EMA50"], 2),
        "EMA200": round(latest["EMA200"], 2),
        "ATR": round(latest["ATR"], 2),
        "ADX": round(latest["ADX"], 2)
    }

    st.dataframe(
    pd.DataFrame(
        indicator_data.items(),
        columns=["Indicator", "Value"]
    ),
    width="stretch"
    )

    # =========================
    # MULTI TIMEFRAME ANALYSIS
    # =========================

    st.subheader("Multi-Timeframe Analysis")

    timeframes = {
        "1 Min": ("1m", "7d"),
        "5 Min": ("5m", "30d"),
        "15 Min": ("15m", "60d"),
        "30 Min": ("30m", "60d"),
        "1 Hour": ("60m", "730d"),
        "1 Day": ("1d", "2y")
    }

    results = []

    for name, (interval, period) in timeframes.items():

        try:
            result = analyze_timeframe(
                symbol,
                interval,
                period
            )

            if result:
                results.append({
                    "Timeframe": name,
                    **result
                })

        except Exception as e:
            results.append({
                "Timeframe": name,
                "Trend": "Error",
                "Signal": str(e),
                "RSI": "",
                "ADX": ""
            })

    st.dataframe(
    pd.DataFrame(results),
    width="stretch"
    )

    st.subheader("Signal Explanation")

    for reason in reasons:
        st.markdown(f"✓ {reason}")

    # =========================
    # PRICE CHART
    # =========================

    st.subheader("Price Chart")

    st.line_chart(df["Close"])

    # =========================
    # LAST 10 CANDLES
    # =========================

    st.subheader("Recent Market Data")

    st.dataframe(
    df.tail(10),
    width="stretch"
    )