def detect_pattern(df):

    if len(df) < 2:
        return "No Pattern"

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # Bullish Engulfing
    if (
        prev["Close"] < prev["Open"]
        and curr["Close"] > curr["Open"]
        and curr["Close"] > prev["Open"]
    ):
        return "Bullish Engulfing"

    # Bearish Engulfing
    if (
        prev["Close"] > prev["Open"]
        and curr["Close"] < curr["Open"]
        and curr["Open"] > prev["Close"]
    ):
        return "Bearish Engulfing"

    # Doji
    body = abs(curr["Close"] - curr["Open"])

    candle_range = curr["High"] - curr["Low"]

    if candle_range > 0:

        if body / candle_range < 0.1:
            return "Doji"

    return "No Clear Pattern"