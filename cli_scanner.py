#!/usr/bin/env python
"""
Live Market Scanner CLI
Scan stocks for trading signals via command line
"""

import argparse
import sys
import time
import pandas as pd
from datetime import datetime
from pathlib import Path

from scanner.market_scanner import scan_market
from scanner.stocks import NIFTY50
from notifications.telegram_alert import send_telegram_alert


# ===========================
# COLORS FOR CLI OUTPUT
# ===========================
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}{Colors.RESET}\n")


def print_signal(row, index):
    """Print a signal row with colors"""
    signal = row["Signal"]

    # Color coding
    if signal in ["BUY", "STRONG BUY"]:
        color = Colors.GREEN
        emoji = "🟢"
    elif signal in ["SELL", "STRONG SELL"]:
        color = Colors.RED
        emoji = "🔴"
    else:
        color = Colors.YELLOW
        emoji = "⚪"

    print(
        f"{index+1:2d}. {color}{emoji} {row['Symbol']:12s} | "
        f"{signal:12s} | Conf: {row['Confidence']:5.1f}% | "
        f"Net: {row['Net Score']:+6.2f} | "
        f"Buy: {row['Buy Score']:6.2f} | Sell: {row['Sell Score']:6.2f}"
        f"{Colors.RESET}"
    )


def print_summary(results_df, min_confidence):
    """Print summary statistics"""
    if results_df.empty:
        print(f"{Colors.YELLOW}No signals found.{Colors.RESET}\n")
        return

    filtered_df = results_df[results_df["Confidence"] >= min_confidence]

    if filtered_df.empty:
        print(
            f"{Colors.YELLOW}No signals meet confidence threshold of {min_confidence}%"
            f"{Colors.RESET}\n"
        )
        return

    print_header("SCAN RESULTS")

    # Summary metrics
    buy_signals = len(
        filtered_df[filtered_df["Signal"].isin(["BUY", "STRONG BUY"])]
    )
    sell_signals = len(
        filtered_df[filtered_df["Signal"].isin(["SELL", "STRONG SELL"])]
    )
    hold_signals = len(filtered_df[filtered_df["Signal"] == "HOLD"])

    print(f"{Colors.GREEN}BUY Signals:  {buy_signals}{Colors.RESET}")
    print(f"{Colors.RED}SELL Signals: {sell_signals}{Colors.RESET}")
    print(f"{Colors.YELLOW}HOLD Signals: {hold_signals}{Colors.RESET}")
    print(f"Total: {len(filtered_df)} signals\n")

    avg_confidence = filtered_df["Confidence"].mean()
    print(f"Average Confidence: {avg_confidence:.1f}%\n")

    # Detailed results
    print(f"{Colors.BOLD}Signal Details:{Colors.RESET}\n")
    print(
        f"{'#':2s} {'Symbol':12s} | {'Signal':12s} | "
        f"{'Confidence':>8s} | {'Net Score':>9s} | "
        f"{'Buy Score':>8s} | {'Sell Score':>10s}"
    )
    print("-" * 80)

    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        print_signal(row, idx)

    print()


def save_results(results_df, output_format, output_file):
    """Save results to file"""
    if results_df.empty:
        print(f"{Colors.YELLOW}No results to save.{Colors.RESET}")
        return

    try:
        if output_format == "csv":
            results_df.to_csv(output_file, index=False)
        elif output_format == "json":
            results_df.to_json(output_file)
        elif output_format == "excel":
            results_df.to_excel(output_file, index=False)

        print(
            f"{Colors.GREEN}Results saved to: {output_file}{Colors.RESET}"
        )

    except Exception as e:
        print(f"{Colors.RED}Error saving results: {e}{Colors.RESET}")


def main():
    """Main CLI handler"""

    parser = argparse.ArgumentParser(
        description="Live Market Scanner - Scan stocks for trading signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan NIFTY50 with default settings
  python cli_scanner.py

  # Scan specific symbols
  python cli_scanner.py -s RELIANCE.NS TCS.NS INFY.NS

  # Scan with custom confidence threshold
  python cli_scanner.py --min-confidence 80

  # Continuous scanning every 5 minutes
  python cli_scanner.py --loop --interval 300

  # Export results to CSV
  python cli_scanner.py -o results.csv --format csv

  # Scan with Telegram alerts
  python cli_scanner.py --telegram --min-confidence 80
        """
    )

    # Arguments
    parser.add_argument(
        "-s", "--symbols",
        nargs="+",
        default=None,
        help="Stock symbols to scan (default: NIFTY50)"
    )

    parser.add_argument(
        "--min-confidence",
        type=int,
        default=70,
        help="Minimum confidence threshold (default: 70)"
    )

    parser.add_argument(
        "-l", "--loop",
        action="store_true",
        help="Run continuous scanning loop"
    )

    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=300,
        help="Scan interval in seconds (default: 300)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file path"
    )

    parser.add_argument(
        "--format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output format (default: csv)"
    )

    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Send Telegram alerts for high-confidence signals"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Determine symbols
    if args.symbols:
        symbols = args.symbols
    else:
        symbols = NIFTY50
        print(
            f"{Colors.CYAN}Using NIFTY50 watchlist ({len(NIFTY50)} symbols)"
            f"{Colors.RESET}"
        )

    print(f"{Colors.CYAN}Starting scanner with {len(symbols)} symbol(s)...{Colors.RESET}")

    # Single or loop scan
    if args.loop:
        print_header(f"CONTINUOUS SCAN (Every {args.interval}s - Press Ctrl+C to stop)")

        try:
            iteration = 0
            while True:
                iteration += 1
                print(
                    f"{Colors.BLUE}Scan #{iteration} - "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
                )

                results_df = scan_market(symbols)
                print_summary(results_df, args.min_confidence)

                # Telegram alerts
                if args.telegram and not results_df.empty:
                    filtered = results_df[
                        results_df["Confidence"] >= args.min_confidence
                    ]
                    for _, row in filtered.iterrows():
                        if row["Confidence"] >= 80:
                            send_telegram_alert(
                                row["Symbol"],
                                row["Signal"],
                                row["Confidence"]
                            )

                # Wait
                print(
                    f"{Colors.YELLOW}Next scan in {args.interval} seconds..."
                    f"{Colors.RESET}"
                )
                time.sleep(args.interval)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Scanner stopped by user.{Colors.RESET}")
            sys.exit(0)

    else:
        # Single scan
        print_header("MARKET SCAN")
        print(
            f"{Colors.BLUE}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            f"{Colors.RESET}"
        )

        results_df = scan_market(symbols)
        print_summary(results_df, args.min_confidence)

        # Save results
        if args.output:
            save_results(results_df, args.format, args.output)

        # Telegram alerts
        if args.telegram and not results_df.empty:
            filtered = results_df[
                results_df["Confidence"] >= args.min_confidence
            ]
            for _, row in filtered.iterrows():
                if row["Confidence"] >= 80:
                    send_telegram_alert(
                        row["Symbol"],
                        row["Signal"],
                        row["Confidence"]
                    )


if __name__ == "__main__":
    main()
