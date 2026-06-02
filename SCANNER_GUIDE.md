# 📊 Market Scanner - Usage Guide

## Overview

The Live Market Scanner provides two interfaces for scanning stocks for trading signals:
1. **Streamlit Dashboard** - Interactive web UI with real-time visualization
2. **CLI Scanner** - Command-line tool for automation and scripting

---

## 🌐 Streamlit Dashboard

### Quick Start

```bash
streamlit run scanner_dashboard.py
```

Opens at: `http://localhost:8501`

### Features

- **Interactive UI** with real-time data visualization
- **Multiple scan modes**:
  - NIFTY50 (default watchlist)
  - Custom symbols
  - Single symbol analysis
- **Configurable filters**:
  - Confidence threshold
  - Auto-refresh interval
  - Custom symbol lists
- **Rich visualizations**:
  - Signal distribution pie chart
  - Confidence distribution histogram
  - Top signals leaderboard
- **Export options**:
  - CSV download
  - JSON download
- **Multi-timeframe analysis** displayed for each signal

### UI Components

1. **Sidebar Settings**:
   - Select scan mode
   - Set confidence threshold (0-100%)
   - Choose refresh interval (60-600 seconds)
   - Enable/disable auto-refresh

2. **Main Display**:
   - Summary metrics (BUY/SELL/HOLD counts)
   - Detailed signals table
   - Charts and visualizations
   - Export buttons

3. **Signal Details**:
   - Symbol name
   - Signal type (BUY/SELL/HOLD)
   - Confidence percentage
   - Buy/Sell/Net scores
   - Multi-timeframe breakdown

---

## 💻 CLI Scanner

### Quick Start (Default)

```bash
python cli_scanner.py
```

Scans NIFTY50 with default settings (70% confidence threshold).

### Examples

**Scan specific symbols:**
```bash
python cli_scanner.py -s RELIANCE.NS TCS.NS INFY.NS
```

**Lower confidence threshold:**
```bash
python cli_scanner.py --min-confidence 50
```

**Continuous scanning every 5 minutes:**
```bash
python cli_scanner.py --loop --interval 300
```

**Export to CSV:**
```bash
python cli_scanner.py -o results.csv --format csv
```

**Scan with Telegram alerts:**
```bash
python cli_scanner.py --telegram --min-confidence 80
```

**Combine multiple options:**
```bash
python cli_scanner.py \
  -s RELIANCE.NS TCS.NS INFY.NS \
  --min-confidence 75 \
  --loop \
  --interval 600 \
  -o scan_results.csv \
  --format csv \
  --telegram
```

### Command-Line Options

```
-h, --help                    Show help message
-s, --symbols SYMBOLS [...]   Stock symbols to scan (default: NIFTY50)
--min-confidence INT          Confidence threshold 0-100 (default: 70)
-l, --loop                    Run continuous scanning loop
-i, --interval INT            Scan interval in seconds (default: 300)
-o, --output FILE             Output file path
--format {csv,json,excel}     Output format (default: csv)
--telegram                    Send Telegram alerts for high-confidence signals
--verbose                     Verbose output
```

### Output Format

**CLI Output:**
```
============================================================
  MARKET SCAN
============================================================

2026-06-01 21:48:06
BUY Signals:  0
SELL Signals: 1
HOLD Signals: 0
Total: 1 signals

Average Confidence: 71.2%

Signal Details:

#  Symbol       | Signal       | Confidence | Net Score | Buy Score | Sell Score
--------------------------------------------------------------------------------
 1. 🔴 TCS.NS       | SELL         | Conf:  71.2% | Net:  -7.12 | Buy:   0.00 | Sell:   7.12
```

**CSV Export:**
```
Symbol,Signal,Confidence,Buy Score,Sell Score,Net Score
TCS.NS,SELL,71.19,0.0,7.12,-7.12
RELIANCE.NS,HOLD,0.0,0.0,0.0,0.0
```

---

## 📊 Signal Types

| Signal | Meaning | Color |
|--------|---------|-------|
| **STRONG BUY** | High confidence bullish with strong AI backing | 🟢 Green |
| **BUY** | Bullish signal with good confluence | 🟢 Green |
| **HOLD** | Mixed or weak signals | ⚪ White |
| **SELL** | Bearish signal | 🔴 Red |
| **STRONG SELL** | High confidence bearish signal | 🔴 Red |

---

## 🧠 Analysis Components

### Technical Indicators
- **EMA20, EMA50, EMA200** - Trend detection
- **RSI** - Momentum & overbought/oversold
- **MACD** - Trend changes & crossovers
- **ADX** - Trend strength filter
- **Bollinger Bands** - Volatility levels
- **ATR** - Volatility measurement

### Multi-Timeframe Analysis
Analyzes signals across:
- 1m (minute)
- 5m (5-minute)
- 15m (15-minute)
- 30m (30-minute)
- 60m (1-hour)
- 1d (daily)

Weighted scoring ensures longer timeframes have more influence.

### Hybrid Scoring
- **Rule-based logic** - Technical indicator patterns
- **AI model** - XGBoost classifier for direction prediction
- **Confidence scoring** - Combined AI + technical confidence

---

## 🔧 Scheduling & Automation

### Run Scanner Every 5 Minutes (Windows Task Scheduler)

Create a batch file `scan_scheduler.bat`:
```batch
@echo off
cd C:\Users\ATUL PANDEY\TRADING_SOFTWARE
.\venv\Scripts\python.exe cli_scanner.py -s RELIANCE.NS TCS.NS --min-confidence 75 -o data\scan_results.csv
```

Schedule with Task Scheduler to run every 5 minutes during market hours.

### Run Scanner Every Hour (Linux/Mac Cron)

```bash
0 * * * * cd /path/to/TRADING_SOFTWARE && ./venv/bin/python cli_scanner.py -o data/scan_results.csv
```

### Continuous Background Scanning

```bash
python cli_scanner.py \
  --loop \
  --interval 300 \
  --telegram \
  --min-confidence 80 \
  -o data/latest_scan.csv
```

Run in a persistent terminal or background process:
- **Windows**: Use `nohup` or Task Scheduler
- **Linux/Mac**: Use `nohup` or `screen`
- **Docker**: Build a container for deployment

---

## 📲 Telegram Alerts

To use Telegram notifications, configure in `notifications/telegram_alert.py`:

```python
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
```

Alerts are sent for signals with confidence ≥ 80%.

---

## 📈 Best Practices

1. **Start with default settings** - 70% confidence filters out most noise
2. **Use multiple timeframes** - Longer timeframes = more reliable signals
3. **Monitor in batches** - Run scanner every 5-15 minutes, not continuously
4. **Cross-check signals** - Always verify with your own analysis
5. **Set realistic thresholds** - Higher confidence = fewer false signals
6. **Use Telegram alerts** - Get notified of high-confidence signals instantly
7. **Export results** - Keep historical scans for analysis and backtesting

---

## 🚀 Advanced Usage

### Custom Watchlist

Create `scanner/custom_watchlist.py`:
```python
MY_WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS"
]
```

Then use:
```bash
python cli_scanner.py -s $(python -c "from scanner.custom_watchlist import MY_WATCHLIST; print(' '.join(MY_WATCHLIST))")
```

### Performance Analysis

Run multiple scans and analyze:
```bash
python cli_scanner.py -o scan_1.csv
python cli_scanner.py -o scan_2.csv
# Compare results
```

### Integration with Other Tools

Both interfaces output data that can be integrated with:
- Email alerts
- Webhook notifications
- Trading execution systems
- Database logging
- Custom dashboards

---

## ❓ Troubleshooting

**No signals found?**
- Lower the confidence threshold: `--min-confidence 50`
- Check market hours (data only available during trading)
- Verify symbols are correct

**Slow scanning?**
- Reduce number of symbols
- Increase scanning interval
- Run on faster machine

**Telegram alerts not working?**
- Verify bot token and chat ID
- Check notification settings
- Ensure confidence ≥ 80%

**Streamlit dashboard frozen?**
- Clear cache: `streamlit cache clear`
- Reduce refresh interval
- Check internet connection

---

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review `data/latest_scan.csv` for last scan results
3. Run with `--verbose` flag for detailed output

---

**Happy scanning! 📊🚀**
