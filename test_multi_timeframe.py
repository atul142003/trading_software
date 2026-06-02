from ai.multi_timeframe import analyze_timeframe

symbol = "RELIANCE.NS"

timeframes = {
    "1 Min": ("1m", "7d"),
    "5 Min": ("5m", "30d"),
    "15 Min": ("15m", "60d"),
    "30 Min": ("30m", "60d"),
    "1 Hour": ("60m", "730d"),
    "1 Day": ("1d", "2y")
}

print("\n===== MULTI TIMEFRAME =====\n")

for name, (interval, period) in timeframes.items():

    result = analyze_timeframe(
        symbol,
        interval,
        period
    )

    print(name, ":", result)