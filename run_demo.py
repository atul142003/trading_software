from ai.hybrid_engine import hybrid_signal
from indicators.technical import add_indicators
from market_data import download_with_fallback

symbol = "RELIANCE.NS"

print("Running demo scanner...")

df, interval = download_with_fallback(symbol)

if df.empty:
    print("No data from Yahoo Finance. Try again during market hours or check the symbol.")
    raise SystemExit(1)

print(f"Using {interval} data ({len(df)} bars)")

df = add_indicators(df)
latest = df.iloc[-1]

try:
    signal = hybrid_signal(latest)
except Exception as e:
    print("Error:", e)
    signal = None

if signal:
    print("\n===== SIGNAL =====")
    print(signal)
else:
    print("No signal generated")
