import pandas as pd

from indicators.technical import add_indicators
from ai.multi_timeframe_engine import multi_timeframe_signal


# =========================
# LOAD DATA
# =========================
df = pd.read_csv("data/reliance.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)

df = add_indicators(df)

df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

df.dropna(inplace=True)


# =========================
# RUN ENGINE
# =========================
result = multi_timeframe_signal(df)

print("\n===== MULTI TIMEFRAME FUSION =====\n")

print("FINAL SIGNAL :", result["Final Signal"])
print("CONFIDENCE   :", result["Confidence"])
print("BUY SCORE    :", result["Buy Score"])
print("SELL SCORE   :", result["Sell Score"])

print("\n--- TIMEFRAME BREAKDOWN ---")
for tf, res in result["Timeframe Signals"].items():
    print(f"\n{tf}:")
    print(res["Signal"], "|", res["Confidence"], "%")