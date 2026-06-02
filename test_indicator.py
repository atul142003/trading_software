import pandas as pd

from indicators.technical import add_indicators

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

print(
    df[
        [
            "Close",
            "EMA20",
            "EMA50",
            "RSI",
            "MACD"
        ]
    ].tail()
)