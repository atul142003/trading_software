import time
import pandas as pd
import yfinance as yf

from scanner.stocks import NIFTY50
from indicators.technical import add_indicators
from ai.multi_timeframe_engine import multi_timeframe_signal
from notifications.telegram_alert import send_telegram_alert


# =========================
# MARKET SCANNER
# =========================
def scan_market(symbols=None):

    if symbols is None:
        symbols = NIFTY50

    results = []

    for symbol in symbols:

        try:

            print(f"Scanning {symbol}...")

            df = yf.download(
                symbol,
                period="30d",
                interval="5m",
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if df.empty:
                print(f"{symbol}: No data")
                continue

            if hasattr(df.columns, "levels"):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

            # Ensure datetime index
            df.index = pd.to_datetime(df.index)

            if len(df) < 250:
                print(f"{symbol}: Insufficient data")
                continue

            # Add indicators
            # Add indicators
            df = add_indicators(df)

            print("\nDEBUG DATAFRAME")
            print(df.tail(2))
            print(df.columns.tolist())

            # Multi-timeframe analysis
            try:
                signal = multi_timeframe_signal(df)
            except Exception as e:
                print(f"{symbol} MTF ERROR -> {e}")
                import traceback
                traceback.print_exc()
                continue

            if not signal:
               print(f"{symbol}: Signal generation failed")
               continue

            required_keys = [
              "Final Signal",
              "Confidence",
              "Buy Score",
              "Sell Score",
                "Net Score"
            ]

            if not all(k in signal for k in required_keys):
              print(f"{symbol}: Invalid signal format")
              continue

            print("\nDEBUG SIGNAL:")
            print(type(signal))
            print(signal)

            if signal is None:
               print(f"{symbol}: Signal generation failed")
               continue

            print(f"{symbol} -> {signal}")

            results.append({

               "Symbol": symbol,

               "Signal": signal["Final Signal"],

               "Confidence": round(signal["Confidence"], 2),

               "Buy Score": round(signal["Buy Score"], 2),

               "Sell Score": round(signal["Sell Score"], 2),

               "Net Score": round(signal["Net Score"], 2)

            })

        except Exception as e:

            print(f"{symbol} ERROR -> {e}")

    return pd.DataFrame(results)


# =========================
# PROCESS RESULTS
# =========================
def process_scan(scanner_df):

    if scanner_df.empty:

        print("\nNo signals found.")
        return

    # Remove weak signals
    scanner_df = scanner_df[
        scanner_df["Confidence"] >= 70
    ]

    if scanner_df.empty:

        print("\nNo high-confidence signals.")
        return

    # Calculate strength
    scanner_df["Strength"] = (
        scanner_df["Buy Score"]
        - scanner_df["Sell Score"]
    )

    # Sort strongest first
    scanner_df = scanner_df.sort_values(
        by="Strength",
        ascending=False
    )

    # Telegram alerts
    for _, row in scanner_df.iterrows():

        if row["Confidence"] >= 80:

            send_telegram_alert(
                row["Symbol"],
                row["Signal"],
                row["Confidence"]
            )

    print("\n===== LIVE MARKET SCAN =====")
    print(scanner_df)

    # Save scan results
    scanner_df.to_csv(
        "data/latest_scan.csv",
        index=False
    )

    print(
        f"\nSaved {len(scanner_df)} signals -> data/latest_scan.csv"
    )


# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":

    print("\n===== AI MARKET SCANNER STARTED =====\n")

    while True:

        try:

            scanner_df = scan_market()

            process_scan(scanner_df)

            print("\nWaiting 300 seconds...\n")

            time.sleep(300)

        except KeyboardInterrupt:

            print("\nScanner stopped by user.")
            break

        except Exception as e:

            print(f"\nScanner Error: {e}")

            time.sleep(60)