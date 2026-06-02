import yfinance as yf

from indicators.technical import add_indicators
from ai.trend import detect_trend
from ai.signals import generate_signal


def analyze_timeframe(symbol, interval, period):

    df = yf.download(
        symbol,
        interval=interval,
        period=period,
        progress=False
    )

    if len(df) < 50:
        return None

    if hasattr(df.columns, "levels"):
        df.columns = [c[0] for c in df.columns]

    df = add_indicators(df)

    latest = df.iloc[-1]

    trend = detect_trend(latest)

    signal = generate_signal(latest)

    return {
    "Trend": trend,
    "Signal": signal,
    "RSI": round(latest["RSI"], 2),
    "ADX": round(latest["ADX"], 2)
    }