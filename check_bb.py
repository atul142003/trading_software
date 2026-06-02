import pandas as pd
import pandas_ta as ta

df = pd.read_csv("data/reliance.csv")

bb = ta.bbands(df["Close"])

print(bb.columns.tolist())
