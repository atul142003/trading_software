import pandas as pd

from indicators.technical import add_indicators
from ai.hybrid_engine import hybrid_signal

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

df.dropna(inplace=True)

latest = df.iloc[-1]

result = hybrid_signal(latest)

print("\n===== HYBRID AI SIGNAL =====\n")

print("Signal     :", result["Signal"])
print("Score      :", result["Score"])
print("Confidence :", result["Confidence"], "%")
print("AI         :", result["AI Direction"], result["AI Confidence"], "%")

print("\n--- Reasons ---")
for r in result["Reasons"]:
    print("•", r)