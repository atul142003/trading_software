import yfinance as yf

symbol = "RELIANCE.NS"

df = yf.download(
    symbol,
    period="2y",
    interval="1d"
)

# Flatten MultiIndex columns if present
if hasattr(df.columns, "levels"):
    df.columns = [col[0] for col in df.columns]

df.to_csv("data/reliance.csv")

print("Data saved successfully")
print(df.tail())