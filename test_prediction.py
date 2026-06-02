import pandas as pd

from indicators.technical import add_indicators
from ai.predict import predict_direction

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

latest = df.iloc[-1]

features = [
    latest["RSI"],
    latest["EMA20"],
    latest["EMA50"],
    latest["MACD"]
]

direction, confidence = predict_direction(features)

print("\n===== AI PREDICTION =====")

print("Direction :", direction)

print("Confidence:", confidence, "%")
