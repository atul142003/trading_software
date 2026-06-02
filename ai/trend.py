def detect_trend(row):

    if row["EMA20"] > row["EMA50"]:
        return "Bullish"

    elif row["EMA20"] < row["EMA50"]:
        return "Bearish"

    return "Sideways"