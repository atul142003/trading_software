import numpy as np
import pandas as pd


def _flatten_ohlcv_columns(df):
    """Normalize yfinance frames (MultiIndex columns) for indicator math."""
    if df is None or df.empty:
        return df
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    elif hasattr(df.columns, "levels"):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in ("open", "high", "low", "close", "volume", "adj close"):
            rename[col] = key.title() if key != "adj close" else "Adj Close"
    if rename:
        df = df.rename(columns=rename)
    return df


def add_indicators(df):

    df = _flatten_ohlcv_columns(df)

    # Trend - EMA
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # Momentum - RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Volatility - ATR
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(window=14).mean()

    # Trend Strength - ADX
    df["+DM"] = df["High"] - df["High"].shift()
    df["-DM"] = df["Low"].shift() - df["Low"]
    df["+DM"] = df["+DM"].where((df["+DM"] > 0) & (df["+DM"] > df["-DM"]), 0)
    df["-DM"] = df["-DM"].where((df["-DM"] > 0) & (df["-DM"] > df["+DM"]), 0)
    tr = true_range
    df["+DI"] = 100 * (df["+DM"].ewm(span=14).mean() / tr.ewm(span=14).mean())
    df["-DI"] = 100 * (df["-DM"].ewm(span=14).mean() / tr.ewm(span=14).mean())
    df["DX"] = 100 * np.abs(df["+DI"] - df["-DI"]) / (df["+DI"] + df["-DI"])
    df["ADX"] = df["DX"].ewm(span=14).mean()

    # Bollinger Bands
    df["BB_MIDDLE"] = df["Close"].rolling(window=20).mean()
    df["BB_STD"] = df["Close"].rolling(window=20).std()
    df["BB_UPPER"] = df["BB_MIDDLE"] + (df["BB_STD"] * 2)
    df["BB_LOWER"] = df["BB_MIDDLE"] - (df["BB_STD"] * 2)

    # Price change & trend strength features
    df["Price_change"] = df["Close"].pct_change().fillna(0)
    df["TF_strength"] = (
        df["EMA20"] - df["EMA50"]
    ).abs() / df["Close"]

    df["EMA_diff"] = df["EMA20"] - df["EMA50"]

    # Clean up temporary columns
    df = df.drop(columns=["+DM", "-DM", "+DI", "-DI", "DX", "BB_STD"], errors="ignore")

    return df