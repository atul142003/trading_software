import pandas as pd

from indicators.technical import add_indicators
from ai.predict_xgb import predict_xgb

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

df.dropna(inplace=True)

latest = df.iloc[-1]

close_price = max(float(latest["Close"]), 0.0001)

features = [
    latest["RSI"] / 100,
    latest["EMA20"] / close_price,
    latest["EMA50"] / close_price,
    latest["EMA200"] / close_price,
    latest["MACD"],
    latest["MACD_SIGNAL"],
    latest["ATR"] / close_price,
    latest["ADX"] / 100,
    latest["BB_UPPER"] / close_price,
    latest["BB_LOWER"] / close_price,
    (latest["EMA20"] - latest["EMA50"]) / close_price,
    latest["Price_change"]
]

direction, confidence = predict_xgb(features)

print("\n===== XGBOOST PREDICTION =====")
print("Direction :", direction)
print("Confidence:", round(confidence, 2), "%")