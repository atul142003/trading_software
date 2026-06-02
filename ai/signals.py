def generate_signal(row):

    if (
        row["EMA20"] > row["EMA50"]
        and row["RSI"] > 55
        and row["MACD"] > 0
    ):
        return "BUY"

    elif (
        row["EMA20"] < row["EMA50"]
        and row["RSI"] < 45
        and row["MACD"] < 0
    ):
        return "SELL"

    return "HOLD"