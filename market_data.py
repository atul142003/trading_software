"""Shared helpers for downloading and normalizing Yahoo Finance OHLCV data."""

import pandas as pd
import yfinance as yf
import io
import time
from functools import lru_cache
from datetime import datetime, timedelta

# Optional backtesting dependencies
try:
    from backtesting import Backtest
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False

# Optional PDF export dependencies
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Optional Excel export dependencies
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    elif hasattr(df.columns, "levels"):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def download_ohlcv(
    symbol: str,
    period: str = "60d",
    interval: str = "5m",
    **kwargs,
) -> pd.DataFrame:
    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        **kwargs,
    )
    return flatten_yfinance_columns(df)


def download_with_fallback(
    symbol: str,
    attempts=None,
    min_rows: int = 50,
) -> tuple[pd.DataFrame, str | None]:
    """Try multiple period/interval pairs; return (df, interval_used)."""
    if attempts is None:
        attempts = [("60d", "5m"), ("2y", "1d")]

    for period, interval in attempts:
        df = download_ohlcv(symbol, period=period, interval=interval)
        if not df.empty and len(df) >= min_rows:
            return df, interval

    return pd.DataFrame(), None


# Rate limiting cache
_live_data_cache = {}
_last_request_time = {}
_rate_limit_delay = 5  # seconds between requests (increased to avoid rate limiting)


def get_live_market_data(symbol: str, use_cache: bool = True) -> dict:
    """Get real-time market data for a symbol with rate limiting and caching."""
    
    # Check cache first
    cache_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d-%H')}"  # Cache per hour
    if use_cache and cache_key in _live_data_cache:
        cached_time = _live_data_cache[cache_key]['timestamp']
        # Use cache if less than 5 minutes old
        if datetime.now() - cached_time < timedelta(minutes=5):
            return _live_data_cache[cache_key]['data']
    
    # Rate limiting: check last request time
    if symbol in _last_request_time:
        time_since_last = (datetime.now() - _last_request_time[symbol]).total_seconds()
        if time_since_last < _rate_limit_delay:
            time.sleep(_rate_limit_delay - time_since_last)
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Try to get info with rate limiting
        try:
            info = ticker.info
        except Exception as e:
            if "Too Many Requests" in str(e) or "rate limit" in str(e).lower():
                # Return cached data if available, or error
                if cache_key in _live_data_cache:
                    return _live_data_cache[cache_key]['data']
                return {
                    "symbol": symbol,
                    "error": "Rate limited. Please wait a few minutes before trying again."
                }
            raise
        
        # Get the most recent price data with fallback
        try:
            df = ticker.history(period="1d", interval="1m")
            if df.empty:
                df = ticker.history(period="5d", interval="1d")
        except Exception as e:
            if "Too Many Requests" in str(e) or "rate limit" in str(e).lower():
                df = pd.DataFrame()
            else:
                raise
        
        if not df.empty:
            latest = df.iloc[-1]
            current_price = latest['Close']
            prev_close = info.get('previousClose', latest['Open'])
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            volume = latest['Volume']
        else:
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', 0)
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            volume = info.get('volume', 0)
        
        result = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(volume),
            "high": info.get('dayHigh', 0),
            "low": info.get('dayLow', 0),
            "open": info.get('regularMarketOpen', 0),
            "prev_close": prev_close,
            "market_cap": info.get('marketCap', 0),
            "52w_high": info.get('fiftyTwoWeekHigh', 0),
            "52w_low": info.get('fiftyTwoWeekLow', 0),
        }
        
        # Update cache
        _live_data_cache[cache_key] = {
            'data': result,
            'timestamp': datetime.now()
        }
        _last_request_time[symbol] = datetime.now()
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
            # Return cached data if available
            if cache_key in _live_data_cache:
                return _live_data_cache[cache_key]['data']
            return {
                "symbol": symbol,
                "error": "Rate limited. Please wait a few minutes before trying again."
            }
        return {
            "symbol": symbol,
            "error": f"Error fetching data: {error_msg}"
        }


def run_backtest(df, strategy, cash=100000, commission=0.002):
    """Run backtesting on the given dataframe with the specified strategy."""
    if not BACKTESTING_AVAILABLE:
        return {
            "error": "backtesting library is not installed. Install it with: pip install backtesting"
        }
    
    try:
        from strategies.strategy import EMARSIMACDStrategy
        
        # Ensure dataframe has required columns
        df_clean = df.copy()
        df_clean = df_clean.dropna()
        
        bt = Backtest(
            df_clean,
            EMARSIMACDStrategy,
            cash=cash,
            commission=commission
        )
        
        stats = bt.run()
        
        # Extract trade history
        trades = stats['_trades'].copy() if '_trades' in stats else pd.DataFrame()
        
        # Extract key metrics
        return {
            "Return (%)": round(stats['Return [%]'], 2),
            "Sharpe Ratio": round(stats['Sharpe Ratio'], 2),
            "Max Drawdown (%)": round(stats['Max. Drawdown [%]'], 2),
            "Win Rate (%)": round(stats['Win Rate [%]'], 2),
            "Total Trades": stats['# Trades'],
            "Avg Trade (%)": round(stats['Avg. Trade [%]'], 2),
            "Best Trade (%)": round(stats['Best Trade [%]'], 2),
            "Worst Trade (%)": round(stats['Worst Trade [%]'], 2),
            "Profit Factor": round(stats['Profit Factor'], 2),
            "Expectancy": round(stats['Expectancy [%]'], 2),
            "Final Equity": round(stats['Equity Final [$]'], 2),
            "Avg Trade Duration": stats['Avg. Trade Duration'],
            "trades": trades
        }
    except Exception as e:
        return {
            "error": str(e)
        }


class Portfolio:
    """Simple portfolio tracking class."""
    
    def __init__(self):
        self.positions = {}  # {symbol: {'quantity': int, 'avg_price': float}}
        self.cash = 100000  # Initial cash
    
    def add_position(self, symbol: str, quantity: int, price: float):
        """Add or update a position."""
        if symbol in self.positions:
            # Calculate new average price
            old_qty = self.positions[symbol]['quantity']
            old_avg = self.positions[symbol]['avg_price']
            total_cost = (old_qty * old_avg) + (quantity * price)
            new_qty = old_qty + quantity
            new_avg = total_cost / new_qty if new_qty > 0 else 0
            self.positions[symbol] = {'quantity': new_qty, 'avg_price': new_avg}
        else:
            self.positions[symbol] = {'quantity': quantity, 'avg_price': price}
        
        self.cash -= quantity * price
    
    def remove_position(self, symbol: str, quantity: int, price: float):
        """Remove or reduce a position."""
        if symbol not in self.positions:
            return False
        
        current_qty = self.positions[symbol]['quantity']
        if quantity > current_qty:
            return False
        
        self.positions[symbol]['quantity'] -= quantity
        self.cash += quantity * price
        
        if self.positions[symbol]['quantity'] == 0:
            del self.positions[symbol]
        
        return True
    
    def get_portfolio_value(self, current_prices: dict) -> dict:
        """Calculate portfolio value with current prices."""
        total_value = self.cash
        positions_value = {}
        
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol, pos['avg_price'])
            position_value = pos['quantity'] * current_price
            positions_value[symbol] = {
                'quantity': pos['quantity'],
                'avg_price': pos['avg_price'],
                'current_price': current_price,
                'position_value': position_value,
                'pnl': position_value - (pos['quantity'] * pos['avg_price']),
                'pnl_percent': ((current_price - pos['avg_price']) / pos['avg_price'] * 100) if pos['avg_price'] > 0 else 0
            }
            total_value += position_value
        
        return {
            'cash': self.cash,
            'positions': positions_value,
            'total_value': total_value,
            'total_pnl': total_value - 100000,  # Assuming 100000 initial investment
            'total_pnl_percent': ((total_value - 100000) / 100000 * 100) if 100000 > 0 else 0
        }
    
    def get_positions_summary(self) -> pd.DataFrame:
        """Get summary of all positions."""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for symbol, pos in self.positions.items():
            data.append({
                'Symbol': symbol,
                'Quantity': pos['quantity'],
                'Avg Price': round(pos['avg_price'], 2),
                'Invested': round(pos['quantity'] * pos['avg_price'], 2)
            })
        
        return pd.DataFrame(data)


def get_portfolio_summary(portfolio: Portfolio) -> dict:
    """Get portfolio summary with current market prices."""
    current_prices = {}
    
    # Fetch current prices for all positions
    for symbol in portfolio.positions.keys():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_prices[symbol] = info.get('currentPrice', info.get('regularMarketPrice', 0))
        except:
            current_prices[symbol] = portfolio.positions[symbol]['avg_price']
    
    return portfolio.get_portfolio_value(current_prices)


def calculate_position_size(
    account_balance: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float
) -> dict:
    """Calculate optimal position size based on risk management rules."""
    if stop_loss_price >= entry_price:
        return {
            "error": "Stop loss must be below entry price for long positions"
        }
    
    risk_per_share = entry_price - stop_loss_price
    if risk_per_share <= 0:
        return {
            "error": "Invalid risk per share calculation"
        }
    
    max_risk_amount = account_balance * (risk_per_trade / 100)
    position_size = max_risk_amount / risk_per_share
    position_value = position_size * entry_price
    
    return {
        "position_size": int(position_size),
        "position_value": round(position_value, 2),
        "risk_amount": round(max_risk_amount, 2),
        "risk_per_share": round(risk_per_share, 2),
        "risk_percentage": risk_per_trade
    }


def calculate_stop_loss(
    entry_price: float,
    atr: float,
    atr_multiplier: float = 2.0,
    method: str = "atr"
) -> dict:
    """Calculate stop loss level using different methods."""
    if method == "atr":
        stop_loss = entry_price - (atr * atr_multiplier)
        stop_loss_pct = ((entry_price - stop_loss) / entry_price) * 100
    elif method == "percentage":
        stop_loss_pct = atr  # atr is used as percentage here
        stop_loss = entry_price * (1 - stop_loss_pct / 100)
    elif method == "support":
        # For support method, atr is the support level
        stop_loss = atr
        stop_loss_pct = ((entry_price - stop_loss) / entry_price) * 100
    else:
        return {
            "error": "Invalid method. Use 'atr', 'percentage', or 'support'"
        }
    
    return {
        "stop_loss_price": round(stop_loss, 2),
        "stop_loss_pct": round(stop_loss_pct, 2),
        "method": method
    }


def calculate_take_profit(
    entry_price: float,
    stop_loss_price: float,
    risk_reward_ratio: float = 2.0
) -> dict:
    """Calculate take profit level based on risk-reward ratio."""
    risk = entry_price - stop_loss_price
    reward = risk * risk_reward_ratio
    take_profit = entry_price + reward
    take_profit_pct = ((take_profit - entry_price) / entry_price) * 100
    
    return {
        "take_profit_price": round(take_profit, 2),
        "take_profit_pct": round(take_profit_pct, 2),
        "risk_reward_ratio": risk_reward_ratio
    }


def calculate_portfolio_risk(portfolio: Portfolio, current_prices: dict) -> dict:
    """Calculate portfolio-level risk metrics."""
    if not portfolio.positions:
        return {
            "total_exposure": 0,
            "concentration_risk": {},
            "portfolio_beta": 0
        }
    
    total_value = portfolio.get_portfolio_value(current_prices)['total_value']
    total_exposure = total_value - portfolio.cash
    
    # Calculate concentration risk
    concentration = {}
    for symbol, pos_data in portfolio.positions.items():
        position_value = pos_data['quantity'] * current_prices.get(symbol, pos_data['avg_price'])
        concentration[symbol] = round((position_value / total_value) * 100, 2)
    
    return {
        "total_exposure": round(total_exposure, 2),
        "cash_ratio": round((portfolio.cash / total_value) * 100, 2),
        "concentration_risk": concentration,
        "number_of_positions": len(portfolio.positions)
    }


def export_to_excel(data: dict, filename: str = "trading_report.xlsx") -> bytes:
    """Export trading data to Excel file."""
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is not installed. Install it with: pip install openpyxl")
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Export each dataframe in the data dict
        for sheet_name, df in data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=True)
            elif isinstance(df, dict):
                # Convert dict to dataframe
                pd.DataFrame([df]).to_excel(writer, sheet_name=sheet_name, index=False)
    
    output.seek(0)
    return output.getvalue()


def export_to_pdf(data: dict, title: str = "Trading Report") -> bytes:
    """Export trading data to PDF file."""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Install it with: pip install reportlab")
    
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title_paragraph = Paragraph(title, styles['Title'])
    story.append(title_paragraph)
    story.append(Spacer(1, 12))
    
    # Add data sections
    for section_name, section_data in data.items():
        # Section header
        header = Paragraph(section_name, styles['Heading2'])
        story.append(header)
        story.append(Spacer(1, 6))
        
        if isinstance(section_data, pd.DataFrame):
            # Convert dataframe to table
            data_rows = [section_data.columns.tolist()] + section_data.values.tolist()
            table = Table(data_rows)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        elif isinstance(section_data, dict):
            # Convert dict to table
            data_rows = [[k, str(v)] for k, v in section_data.items()]
            table = Table(data_rows, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        
        story.append(Spacer(1, 12))
    
    doc.build(story)
    output.seek(0)
    return output.getvalue()


def get_model_accuracy_metrics() -> dict:
    """Get model accuracy metrics from the accuracy report."""
    try:
        # These are the metrics from the ACCURACY_REPORT.md
        return {
            "model_accuracy": 55.93,
            "precision": 32.26,
            "recall": 66.67,
            "f1_score": 43.48,
            "roc_auc": 63.33,
            "cv_accuracy": 36.60,
            "cv_std": 16.56,
            "specificity": 52.27,
            "sensitivity": 66.67,
            "backtest_return": 105.40,
            "buy_hold_return": 11.21,
            "win_rate": 58.70,
            "outperformance": 94.19
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def track_prediction_accuracy(predictions: list, actuals: list) -> dict:
    """Track and calculate prediction accuracy over time."""
    if len(predictions) != len(actuals):
        return {"error": "Predictions and actuals must have same length"}
    
    correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
    total = len(predictions)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    # Calculate precision, recall, f1
    true_positives = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 1)
    false_positives = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 0)
    false_negatives = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 1)
    
    precision = (true_positives / (true_positives + false_positives) * 100) if (true_positives + false_positives) > 0 else 0
    recall = (true_positives / (true_positives + false_negatives) * 100) if (true_positives + false_negatives) > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
    
    return {
        "accuracy": round(accuracy, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1_score": round(f1, 2),
        "total_predictions": total,
        "correct_predictions": correct
    }
