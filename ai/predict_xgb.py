import joblib
import pandas as pd
import numpy as np

model = joblib.load("models/xgb_model.pkl")


def predict_xgb(row):

    close_price = max(float(row["Close"]), 0.0001)

    X = pd.DataFrame([{
        "RSI_N": row["RSI"] / 100,
        "EMA20_N": row["EMA20"] / close_price,
        "EMA50_N": row["EMA50"] / close_price,
        "EMA200_N": row["EMA200"] / close_price,
        "MACD": row["MACD"],
        "MACD_SIGNAL": row["MACD_SIGNAL"],
        "ATR_N": row["ATR"] / close_price,
        "ADX_N": row["ADX"] / 100,
        "BB_UPPER_N": row["BB_UPPER"] / close_price,
        "BB_LOWER_N": row["BB_LOWER"] / close_price,
        "EMA_DIFF_N": (row["EMA20"] - row["EMA50"]) / close_price,
        "Price_change": row["Price_change"]
    }])

    prob = model.predict_proba(X)[0]

    pred = model.predict(X)[0]

    confidence = float(np.max(prob)) * 100

    direction = "UP" if pred == 1 else "DOWN"

    return direction, confidence