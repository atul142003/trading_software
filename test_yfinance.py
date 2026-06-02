import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")

df = ticker.history(period="5d")

print(df)
print("\nRows:", len(df))