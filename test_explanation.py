import pandas as pd

from indicators.technical import add_indicators
from ai.explain import explain_signal

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

latest = df.iloc[-1]

reasons = explain_signal(latest)

print("\n===== SIGNAL EXPLANATION =====\n")

for reason in reasons:
    print("-", reason)