def detect_pattern(df):

    if len(df) < 2:
        return "No Pattern"

    prev = df.iloc[-2]
    curr = df.iloc[-1]
    
    # Calculate body and range
    prev_body = abs(prev["Close"] - prev["Open"])
    curr_body = abs(curr["Close"] - curr["Open"])
    prev_range = prev["High"] - prev["Low"]
    curr_range = curr["High"] - curr["Low"]
    
    # Calculate upper and lower shadows
    curr_upper_shadow = curr["High"] - max(curr["Open"], curr["Close"])
    curr_lower_shadow = min(curr["Open"], curr["Close"]) - curr["Low"]
    
    # Calculate average body for comparison
    if len(df) >= 10:
        avg_body = df.iloc[-10:]["Close"].sub(df.iloc[-10:]["Open"]).abs().mean()
    else:
        avg_body = (prev_body + curr_body) / 2

    # Bullish Engulfing
    if (
        prev["Close"] < prev["Open"]
        and curr["Close"] > curr["Open"]
        and curr["Close"] > prev["Open"]
        and curr["Open"] < prev["Close"]
    ):
        return "Bullish Engulfing"

    # Bearish Engulfing
    if (
        prev["Close"] > prev["Open"]
        and curr["Close"] < curr["Open"]
        and curr["Open"] > prev["Close"]
        and curr["Close"] < prev["Open"]
    ):
        return "Bearish Engulfing"

    # Doji
    if curr_range > 0 and curr_body / curr_range < 0.1:
        return "Doji"

    # Hammer (Bullish)
    if (
        curr_lower_shadow > 2 * curr_body
        and curr_upper_shadow < curr_body * 0.5
        and curr["Close"] > curr["Open"]
        and len(df) >= 5
    ):
        # Check if in downtrend
        if df.iloc[-5]["Close"] > df.iloc[-1]["Close"]:
            return "Hammer"

    # Inverted Hammer (Bullish)
    if (
        curr_upper_shadow > 2 * curr_body
        and curr_lower_shadow < curr_body * 0.5
        and curr["Close"] > curr["Open"]
        and len(df) >= 5
    ):
        if df.iloc[-5]["Close"] > df.iloc[-1]["Close"]:
            return "Inverted Hammer"

    # Shooting Star (Bearish)
    if (
        curr_upper_shadow > 2 * curr_body
        and curr_lower_shadow < curr_body * 0.5
        and curr["Close"] < curr["Open"]
        and len(df) >= 5
    ):
        if df.iloc[-5]["Close"] < df.iloc[-1]["Close"]:
            return "Shooting Star"

    # Hanging Man (Bearish)
    if (
        curr_lower_shadow > 2 * curr_body
        and curr_upper_shadow < curr_body * 0.5
        and curr["Close"] < curr["Open"]
        and len(df) >= 5
    ):
        if df.iloc[-5]["Close"] < df.iloc[-1]["Close"]:
            return "Hanging Man"

    # Morning Star (Bullish) - requires 3 candles
    if len(df) >= 3:
        day_before = df.iloc[-3]
        yesterday = df.iloc[-2]
        today = df.iloc[-1]
        
        if (
            day_before["Close"] < day_before["Open"]  # Bearish first day
            and abs(yesterday["Close"] - yesterday["Open"]) < avg_body * 0.3  # Small body middle day
            and today["Close"] > today["Open"]  # Bullish third day
            and today["Close"] > (day_before["Open"] + day_before["Close"]) / 2  # Recovery
        ):
            return "Morning Star"

    # Evening Star (Bearish) - requires 3 candles
    if len(df) >= 3:
        day_before = df.iloc[-3]
        yesterday = df.iloc[-2]
        today = df.iloc[-1]
        
        if (
            day_before["Close"] > day_before["Open"]  # Bullish first day
            and abs(yesterday["Close"] - yesterday["Open"]) < avg_body * 0.3  # Small body middle day
            and today["Close"] < today["Open"]  # Bearish third day
            and today["Close"] < (day_before["Open"] + day_before["Close"]) / 2  # Decline
        ):
            return "Evening Star"

    # Three White Soldiers (Bullish) - requires 3 candles
    if len(df) >= 3:
        if (
            all(df.iloc[-i]["Close"] > df.iloc[-i]["Open"] for i in range(1, 4))
            and all(df.iloc[-i]["Close"] > df.iloc[-i-1]["Close"] for i in range(1, 3))
            and all(df.iloc[-i]["Open"] > df.iloc[-i-1]["Open"] for i in range(1, 3))
        ):
            return "Three White Soldiers"

    # Three Black Crows (Bearish) - requires 3 candles
    if len(df) >= 3:
        if (
            all(df.iloc[-i]["Close"] < df.iloc[-i]["Open"] for i in range(1, 4))
            and all(df.iloc[-i]["Close"] < df.iloc[-i-1]["Close"] for i in range(1, 3))
            and all(df.iloc[-i]["Open"] < df.iloc[-i-1]["Open"] for i in range(1, 3))
        ):
            return "Three Black Crows"

    # Spinning Top
    if (
        curr_body < avg_body * 0.5
        and curr_upper_shadow > curr_body
        and curr_lower_shadow > curr_body
    ):
        return "Spinning Top"

    # Marubozu (Bullish)
    if (
        curr["Close"] > curr["Open"]
        and curr_upper_shadow < curr_body * 0.05
        and curr_lower_shadow < curr_body * 0.05
    ):
        return "Bullish Marubozu"

    # Marubozu (Bearish)
    if (
        curr["Close"] < curr["Open"]
        and curr_upper_shadow < curr_body * 0.05
        and curr_lower_shadow < curr_body * 0.05
    ):
        return "Bearish Marubozu"

    # Piercing Line (Bullish)
    if (
        prev["Close"] < prev["Open"]
        and curr["Close"] > curr["Open"]
        and curr["Open"] < prev["Low"]
        and curr["Close"] > (prev["Open"] + prev["Close"]) / 2
    ):
        return "Piercing Line"

    # Dark Cloud Cover (Bearish)
    if (
        prev["Close"] > prev["Open"]
        and curr["Close"] < curr["Open"]
        and curr["Open"] > prev["High"]
        and curr["Close"] < (prev["Open"] + prev["Close"]) / 2
    ):
        return "Dark Cloud Cover"

    return "No Clear Pattern"