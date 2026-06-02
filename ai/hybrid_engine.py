import joblib
import numpy as np
import pandas as pd

# =========================
# LOAD MODEL
# =========================
model = joblib.load("models/xgb_model.pkl")

print("Features:", model.n_features_in_)

# =========================
# MODEL FEATURE ORDER
# =========================
FEATURE_NAMES = [
    "RSI_N",
    "EMA20_N",
    "EMA50_N",
    "EMA200_N",
    "MACD",
    "MACD_SIGNAL",
    "ATR_N",
    "ADX_N",
    "BB_UPPER_N",
    "BB_LOWER_N",
    "EMA_DIFF_N",
    "Price_change",
    "TF_strength"
]


# =========================
# AI MODEL PREDICTION
# =========================

def get_ai_signal(features):

    X = pd.DataFrame(
        [features],
        columns=FEATURE_NAMES
    )

    prob = model.predict_proba(X)[0]
    prediction = model.predict(X)[0]

    raw_conf = float(np.max(prob)) * 100

    # smoother confidence
    confidence = max(
        20,
        min(95, raw_conf * 0.90)
    )

    direction = "UP" if prediction == 1 else "DOWN"

    return direction, confidence


# =========================
# HYBRID ENGINE
# =========================
def hybrid_signal(row, tf_factor=1.0):

    if isinstance(row, pd.Series):
        row = row.fillna(0)

    # =========================
    # REQUIRED COLUMNS CHECK
    # =========================
    required_cols = [
        "Close",
        "EMA20",
        "EMA50",
        "EMA200",
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "ATR",
        "ADX",
        "BB_UPPER",
        "BB_LOWER",
        "Price_change",
        "TF_strength"
    ]

    for col in required_cols:
        if col not in row.index:
            raise ValueError(f"Missing indicator column: {col}")

    # =========================
    # INDICATOR LOGIC
    # =========================
    ema_bull = row["EMA20"] > row["EMA50"] > row["EMA200"]
    ema_bear = row["EMA20"] < row["EMA50"] < row["EMA200"]

    rsi_bull = row["RSI"] > 52
    rsi_bear = row["RSI"] < 48

    macd_bull = row["MACD"] > row["MACD_SIGNAL"]
    macd_bear = row["MACD"] < row["MACD_SIGNAL"]

    adx_weak = row["ADX"] < 18
    adx_strong = row["ADX"] > 25

    # =========================
    # FEATURE ENGINEERING
    # =========================
    close_price = max(float(row["Close"]), 0.0001)

    ema_diff = (
        row["EMA20"] - row["EMA50"]
    ) * tf_factor

    price_change = (
        row.get("Price_change", 0)
    ) * tf_factor

    features = [
        row["RSI"] / 100,
        row["EMA20"] / close_price,
        row["EMA50"] / close_price,
        row["EMA200"] / close_price,
        row["MACD"],
        row["MACD_SIGNAL"],
        row["ATR"] / close_price,
        row["ADX"] / 100,
        row["BB_UPPER"] / close_price,
        row["BB_LOWER"] / close_price,
        ema_diff / close_price,
        price_change,
        row.get("TF_strength", 0)
    ]

    ai_direction, ai_confidence = get_ai_signal(features)

    # =========================
    # SCORING ENGINE
    # =========================
    score = 0
    reasons = []

    # =========================
    # TREND STRUCTURE
    # =========================
    tf_strength = row.get("TF_strength", None)

    if tf_strength is not None and tf_strength < 0.003:
        score -= 1
        reasons.append("Weak trend structure")

    if row.get("ADX", 0) < 12:
        score -= 1
        reasons.append("Very weak ADX filter")

    # =========================
    # AI CONTRIBUTION
    # =========================
    if ai_direction == "UP" and ai_confidence > 60:
        score += 3
        reasons.append(
            f"AI bullish ({round(ai_confidence,1)}%)"
        )

    elif ai_direction == "DOWN" and ai_confidence > 60:
        score -= 3
        reasons.append(
            f"AI bearish ({round(ai_confidence,1)}%)"
        )

    # =========================
    # EMA TREND
    # =========================
    if ema_bull:
        score += 1.5
        reasons.append("EMA bullish")

    elif ema_bear:
        score -= 1.5
        reasons.append("EMA bearish")

    # =========================
    # RSI
    # =========================
    if rsi_bull:
        score += 1
        reasons.append("RSI bullish")

    elif rsi_bear:
        score -= 1
        reasons.append("RSI bearish")

    # =========================
    # MACD
    # =========================
    if macd_bull:
        score += 1
        reasons.append("MACD bullish crossover")

    elif macd_bear:
        score -= 1
        reasons.append("MACD bearish crossover")

    # =========================
    # ADX FILTER
    # =========================
    if adx_weak:
        score -= 0.5
        reasons.append("Weak trend")

    elif adx_strong:

        if score > 0:
            score += 0.5

        elif score < 0:
            score -= 0.5

        reasons.append("Strong trend")

    # =========================
    # LOW TF CHOP FILTER
    # =========================
    if (
        tf_factor < 0.9
        and abs(row["RSI"] - 50) < 5
    ):
        score -= 1
        reasons.append("Low timeframe chop zone")

    # =========================
    # FINAL SIGNAL LOGIC
    # =========================
    if (
        ai_confidence > 85
        and ai_direction == "UP"
        and ema_bull
        and score >= 5
    ):
        signal = "STRONG BUY"
        confidence = 90

    elif (
        ai_confidence > 85
        and ai_direction == "DOWN"
        and ema_bear
        and score <= -5
    ):
        signal = "STRONG SELL"
        confidence = 90

    elif score >= 3:
        signal = "BUY"
        confidence = min(
            90,
            round(abs(score) * 18)
        )

    elif score <= -3:
        signal = "SELL"
        confidence = min(
            90,
            round(abs(score) * 18)
        )

    else:
        signal = "HOLD"
        confidence = min(
            40,
            round(abs(score) * 10)
        )

    return {
        "Signal": signal,
        "Score": round(score, 2),
        "Confidence": confidence,
        "AI Direction": ai_direction,
        "AI Confidence": round(ai_confidence, 2),
        "Reasons": reasons
    }