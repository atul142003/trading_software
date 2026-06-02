import pandas as pd
import pandas_ta as ta

df = pd.read_csv("data/reliance.csv")

adx = ta.adx(
    df["High"],
    df["Low"],
    df["Close"]
)

print(adx.columns.tolist())