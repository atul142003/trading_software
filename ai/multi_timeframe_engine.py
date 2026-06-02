import pandas as pd
from ai.hybrid_engine import hybrid_signal
from indicators.technical import add_indicators

# =========================
# TIMEFRAME CONFIG
# =========================
TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "60m": "60min",
    "1d": "1D"
}

# =========================
# RESAMPLE DATA
# =========================
def resample_data(df, tf):

    try:

        ohlc = {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }

        tf_df = (
            df.resample(TIMEFRAMES[tf])
            .agg(ohlc)
            .dropna()
        )

        if tf_df.empty:
            return pd.DataFrame()

        tf_df = add_indicators(tf_df)

        tf_df["EMA_diff"] = (
            tf_df["EMA20"] - tf_df["EMA50"]
        )

        tf_df["Price_change"] = (
            tf_df["Close"].pct_change()
        )

        tf_df["Returns"] = (
            tf_df["Close"].pct_change()
        )

        tf_df["Volatility"] = (
            tf_df["Returns"]
            .rolling(10)
            .std()
        )

        tf_df["TF_strength"] = (
            abs(
                tf_df["EMA20"]
                - tf_df["EMA50"]
            )
            / tf_df["Close"]
        )

        tf_df.dropna(inplace=True)

        return tf_df

    except Exception as e:

        print(f"Resample Error ({tf}): {e}")

        return pd.DataFrame()


# =========================
# NORMALIZE CONFIDENCE
# =========================
def normalize_confidence(conf):
    return max(0.0, min(conf, 100.0)) / 100.0


# =========================
# MULTI TIMEFRAME ENGINE (FINAL FIXED)
# =========================
def multi_timeframe_signal(df):
    
    if df is None or len(df) == 0:
        return None

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    df = df.sort_index()

    results = {}

    buy_score = 0.0
    sell_score = 0.0

    weights = {
        "1m": 1,
        "5m": 2,
        "15m": 3,
        "30m": 4,
        "60m": 5,
        "1d": 6
    }

    tf_factor_map = {
        "1m": 0.8,
        "5m": 0.9,
        "15m": 1.0,
        "30m": 1.1,
        "60m": 1.2,
        "1d": 1.3
    }

    valid_timeframes = 0
    
    for tf, weight in weights.items():

        tf_df = resample_data(df, tf)

        if tf_df.empty or len(tf_df) < 50:
            continue

        if tf_df["ADX"].iloc[-1] < 10:
            print(f"{tf}: ignored due to weak ADX")
            continue

        if tf_df["TF_strength"].iloc[-1] < 0.001:
            print(f"{tf}: ignored due to low trend strength")
            continue

        valid_timeframes += 1


        tf_factor = tf_factor_map[tf]

        latest = tf_df.iloc[-1]

        try:
            signal = hybrid_signal(latest, tf_factor)

        except Exception as e:
            print(f"{tf}: hybrid_signal error -> {e}")
            continue

        print(f"{tf} Signal -> {signal}")

        if signal is None:
            print(f"{tf}: hybrid signal failed")
            continue
        
        if not isinstance(signal, dict):
            print(f"{tf}: invalid signal type -> {type(signal)}")
            continue

        required_keys = [
            "Signal",
            "Confidence"
        ]

        if not all(k in signal for k in required_keys):
            print(f"{tf}: missing keys in signal")
            continue

        if tf == "1m":
           signal["Confidence"] *= 0.60

        elif tf == "5m":
           signal["Confidence"] *= 0.75

        # =========================
        # LOW-TIMEFRAME CONFIDENCE PENALTY
        # =========================
        if tf in ["1m", "5m"] and signal["Confidence"] > 85:
           signal["Confidence"] *= 0.7

        results[tf] = signal

        conf = normalize_confidence(signal["Confidence"])

        # =========================
        # WEIGHTED SCORE (IMPROVED)
        # =========================

        directional_strength = weight * conf * tf_factor

        if signal["Signal"] in ["BUY", "STRONG BUY"]:
            buy_score += directional_strength

        elif signal["Signal"] in ["SELL", "STRONG SELL"]:
            sell_score += directional_strength
        


    # AFTER THE FOR LOOP

    # =========================
    # NO VALID TIMEFRAMES
    # =========================
    if valid_timeframes == 0:
        return {
            "Final Signal": "HOLD",
            "Confidence": 0,
            "Buy Score": 0,
            "Sell Score": 0,
            "Net Score": 0,
            "Timeframe Signals": {}
        }

    # =========================
    # FINAL DECISION
    # =========================
    net_score = buy_score - sell_score

    if net_score > 2:
        final_signal = "BUY"

    elif net_score < -2:
        final_signal = "SELL"

    else:
        final_signal = "HOLD"

    confidence = min(
        100,
        round(abs(net_score) * 10, 2)
    )

    return {
        "Final Signal": final_signal,
        "Confidence": confidence,
        "Buy Score": round(buy_score, 2),
        "Sell Score": round(sell_score, 2),
        "Net Score": round(net_score, 2),
        "Timeframe Signals": results
    }