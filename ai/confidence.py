def calculate_confidence(row):

    score = 0

    if row["EMA20"] > row["EMA50"]:
        score += 25

    if row["RSI"] > 55:
        score += 25

    if row["MACD"] > 0:
        score += 25

    if row["ADX"] > 25:
        score += 25

    return score