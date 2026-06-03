import pandas as pd

from indicators.technical import add_indicators
from ai.predict_xgb import predict_xgb

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

df.dropna(inplace=True)

latest = df.iloc[-1]

direction, confidence = predict_xgb(latest)

print("\n===== XGBOOST PREDICTION =====")
print("Direction :", direction)
print("Confidence:", round(confidence, 2), "%")