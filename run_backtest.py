import pandas as pd

from backtesting import Backtest

from indicators.technical import add_indicators

from strategies.strategy import EMARSIMACDStrategy

df = pd.read_csv(
    "data/reliance.csv",
    parse_dates=["Date"]
)

df.set_index("Date", inplace=True)

df = add_indicators(df)

# ADD HERE
print(df.columns.tolist())

df.dropna(inplace=True)

bt = Backtest(
    df,
    EMARSIMACDStrategy,
    cash=100000,
    commission=.002
)

stats = bt.run()

print(stats)

bt.plot()