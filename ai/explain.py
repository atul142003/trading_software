def explain_signal(row):

    reasons = []

    # EMA Trend
    if row["EMA20"] > row["EMA50"]:
        reasons.append("EMA20 above EMA50 (Bullish)")
    else:
        reasons.append("EMA20 below EMA50 (Bearish)")

    # Long-term Trend
    if row["EMA50"] > row["EMA200"]:
        reasons.append("EMA50 above EMA200 (Long-term Bullish)")
    else:
        reasons.append("EMA50 below EMA200 (Long-term Bearish)")

    # RSI
    if row["RSI"] > 55:
        reasons.append("RSI indicates bullish momentum")
    elif row["RSI"] < 45:
        reasons.append("RSI indicates bearish momentum")
    else:
        reasons.append("RSI is neutral")

    # MACD
    if row["MACD"] > 0:
        reasons.append("MACD is positive")
    else:
        reasons.append("MACD is negative")

    # ADX
    if row["ADX"] > 25:
        reasons.append("Strong trend detected")
    else:
        reasons.append("Weak trend detected")

    return reasons