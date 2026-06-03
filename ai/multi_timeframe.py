from indicators.technical import add_indicators
from market_data import download_ohlcv
from ai.trend import detect_trend
from ai.signals import generate_signal


def analyze_timeframe(symbol, interval, period):

    df = download_ohlcv(symbol, interval=interval, period=period)

    if len(df) < 50:
        return None

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