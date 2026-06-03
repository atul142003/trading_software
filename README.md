# AI Trading Software V1.1

A comprehensive AI-powered trading software with technical analysis, portfolio management, risk management, and backtesting capabilities.

## Features

- **Live Market Updates**: Real-time price, volume, and market data with auto-refresh
- **Professional Candlestick Charts**: Interactive Plotly charts with volume bars and moving averages
- **Technical Indicators**: RSI, MACD, EMA (20, 50, 200), ADX, ATR, Bollinger Bands
- **AI Analysis**: Trend detection, signal generation, price prediction, multi-timeframe analysis
- **Pattern Detection**: Candlestick pattern recognition
- **Portfolio Tracking**: Add/remove positions, real-time valuation, P&L tracking
- **Risk Management**: Position sizing calculator, stop loss calculator, take profit calculator, portfolio risk analysis
- **Backtesting**: Strategy backtesting with detailed trade history and performance metrics
- **Model Accuracy Dashboard**: Track AI model performance metrics
- **Export Functionality**: Export analysis, portfolio, and backtest results to PDF/Excel

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd TRADING_SOFTWARE
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development

Run the Streamlit app:
```bash
streamlit run app.py
```

Or using Python:
```bash
python -m streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Deployment

### Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. Configure:
   - Repository: Your GitHub repo
   - Branch: main
   - Main file path: app.py
5. Click "Deploy"

### Docker Deployment

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. Build the Docker image:
```bash
docker build -t ai-trading-software .
```

3. Run the container:
```bash
docker run -p 8501:8501 ai-trading-software
```

### Heroku Deployment

1. Create a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT
```

2. Create a `runtime.txt`:
```
python-3.11
```

3. Deploy to Heroku:
```bash
heroku create your-app-name
git push heroku main
```

## Configuration

### Environment Variables

No environment variables are required for basic functionality. The application uses default settings.

### Customization

You can customize the following in `app.py`:
- Initial portfolio cash (default: ₹100,000)
- Backtest commission rate (default: 0.2%)
- Risk per trade (default: 2%)
- ATR multiplier (default: 2.0)
- Risk-reward ratio (default: 2.0)

## Project Structure

```
TRADING_SOFTWARE/
├── app.py                 # Main Streamlit application
├── market_data.py         # Market data and portfolio functions
├── requirements.txt       # Python dependencies
├── ai/                    # AI analysis modules
│   ├── trend.py          # Trend detection
│   ├── signals.py        # Signal generation
│   ├── predict.py        # Price prediction
│   ├── multi_timeframe.py # Multi-timeframe analysis
│   └── explain.py        # Signal explanation
├── indicators/           # Technical indicators
│   └── technical.py      # Technical indicator calculations
├── patterns/             # Pattern detection
│   └── candles.py       # Candlestick patterns
├── strategies/           # Trading strategies
│   └── strategy.py      # EMA-RSI-MACD strategy
├── models/              # Trained AI models
└── data/                # Data storage
```

## Usage

1. Enter a stock symbol (e.g., TCS.NS, INFY.NS, RELIANCE.NS)
2. Click "Analyze" to run the analysis
3. View the results:
   - Live market data
   - Technical indicators
   - AI predictions and signals
   - Candlestick chart with auto-refresh
   - Portfolio management
   - Risk management calculators
   - Backtesting results
   - Model accuracy metrics

## Dependencies

- pandas
- numpy
- yfinance
- pandas-ta
- plotly
- streamlit
- scikit-learn
- xgboost
- joblib
- matplotlib
- ta
- reportlab (optional - for PDF export)
- openpyxl (optional - for Excel export)
- backtesting (optional - for backtesting)

## Notes

- The application uses Yahoo Finance for market data
- AI models are pre-trained and included in the `models/` directory
- PDF and Excel export features require optional dependencies
- Backtesting requires the backtesting library
- For production use, consider adding authentication and rate limiting

## License

This project is for educational and research purposes only. Not suitable for live trading with real money without proper testing and risk management.

## Disclaimer

This software is provided for educational purposes only. Past performance is not indicative of future results. Always conduct your own research and consult with a financial advisor before making investment decisions.
