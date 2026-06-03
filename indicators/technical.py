import numpy as np
import pandas as pd
import pandas_ta as ta


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

    # Trend
    df["EMA20"] = ta.ema(df["Close"], length=20)
    df["EMA50"] = ta.ema(df["Close"], length=50)
    df["EMA200"] = ta.ema(df["Close"], length=200)

    # Momentum
    df["RSI"] = ta.rsi(df["Close"], length=14)

    # MACD
    macd = ta.macd(df["Close"])
    if macd is None or "MACD_12_26_9" not in macd.columns:
        df["MACD"] = np.nan
        df["MACD_SIGNAL"] = np.nan
    else:
        df["MACD"] = macd["MACD_12_26_9"]
        df["MACD_SIGNAL"] = macd["MACDs_12_26_9"]

    # Volatility
    atr = ta.atr(
        df["High"],
        df["Low"],
        df["Close"]
    )
    df["ATR"] = atr if atr is not None else np.nan

    # Trend Strength
    adx = ta.adx(
        df["High"],
        df["Low"],
        df["Close"]
    )
    df["ADX"] = adx["ADX_14"] if adx is not None and "ADX_14" in adx.columns else np.nan

    # Bollinger Bands
    bb = ta.bbands(df["Close"])
    if bb is None or bb.shape[1] < 3:
        df["BB_LOWER"] = np.nan
        df["BB_MIDDLE"] = np.nan
        df["BB_UPPER"] = np.nan
    else:
        df["BB_LOWER"] = bb.iloc[:, 0]
        df["BB_MIDDLE"] = bb.iloc[:, 1]
        df["BB_UPPER"] = bb.iloc[:, 2]

    # Price change & trend strength features
    df["Price_change"] = df["Close"].pct_change().fillna(0)
    df["TF_strength"] = (
        df["EMA20"] - df["EMA50"]
    ).abs() / df["Close"]

    df["EMA_diff"] = df["EMA20"] - df["EMA50"]

    return df