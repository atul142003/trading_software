"""Download daily OHLCV for a symbol and save to data/reliance.csv."""

from market_data import download_ohlcv

symbol = "RELIANCE.NS"


def main():
    df = download_ohlcv(symbol, period="2y", interval="1d")
    if df.empty:
        print("No data downloaded")
        return

    df.to_csv("data/reliance.csv")
    print("Data saved successfully")
    print(df.tail())


if __name__ == "__main__":
    main()
