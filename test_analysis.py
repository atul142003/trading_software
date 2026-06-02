import pandas as pd

from indicators.technical import add_indicators
from ai.trend import detect_trend
from ai.signals import generate_signal
from patterns.candles import detect_pattern

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

latest = df.iloc[-1]

trend = detect_trend(latest)
signal = generate_signal(latest)
pattern = detect_pattern(df)

print("\n===== ANALYSIS =====")

print("Trend   :", trend)
print("Signal  :", signal)
print("Pattern :", pattern)

print("RSI     :", round(latest["RSI"], 2))
print("EMA20   :", round(latest["EMA20"], 2))
print("EMA50   :", round(latest["EMA50"], 2))
print("MACD    :", round(latest["MACD"], 2))