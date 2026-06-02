import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from xgboost import XGBClassifier

from indicators.technical import add_indicators

# =========================
# LOAD DATA
# =========================

df = pd.read_csv("data/reliance.csv")

df = add_indicators(df)

# =========================
# FEATURE ENGINEERING
# =========================

df["EMA_diff"] = df["EMA20"] - df["EMA50"]

df["Price_change"] = df["Close"].pct_change()

close_safe = df["Close"].replace(0, np.nan)

# =========================
# NORMALIZED FEATURES
# =========================

df["RSI_N"] = df["RSI"] / 100

df["EMA20_N"] = df["EMA20"] / close_safe
df["EMA50_N"] = df["EMA50"] / close_safe
df["EMA200_N"] = df["EMA200"] / close_safe

df["ATR_N"] = df["ATR"] / close_safe

df["ADX_N"] = df["ADX"] / 100

df["BB_UPPER_N"] = df["BB_UPPER"] / close_safe
df["BB_LOWER_N"] = df["BB_LOWER"] / close_safe

df["EMA_DIFF_N"] = df["EMA_diff"] / close_safe

# =========================
# TREND STRENGTH FEATURE
# =========================

df["TF_strength"] = (
    abs(df["EMA20"] - df["EMA50"])
    / close_safe
)

# =========================
# ATR BASED TARGET
# =========================

future_bars = 5

df["Future_Return"] = (
    df["Close"].shift(-future_bars)
    / df["Close"]
    - 1
)

df["Target"] = np.where(
    df["Future_Return"] > (df["ATR_N"] * 0.75),
    1,
    0
)

df.dropna(inplace=True)

# =========================
# TARGET DISTRIBUTION
# =========================

print("\n===== TARGET DISTRIBUTION =====")

print(df["Target"].value_counts())

print("\nNormalized:")

print(df["Target"].value_counts(normalize=True))

print("\nBUY RATE:")

print(round(df["Target"].mean() * 100, 2), "%")

# =========================
# FEATURES
# =========================

FEATURES = [
    "RSI_N",
    "EMA20_N",
    "EMA50_N",
    "EMA200_N",
    "MACD",
    "MACD_SIGNAL",
    "ATR_N",
    "ADX_N",
    "BB_UPPER_N",
    "BB_LOWER_N",
    "EMA_DIFF_N",
    "Price_change",
    "TF_strength"
]

# =========================
# MISSING VALUE CHECK
# =========================

print("\n===== MISSING VALUES =====")

print(
    df[
        FEATURES + ["Target"]
    ].isna().sum()
)

# =========================
# TRAIN DATA
# =========================

X = df[FEATURES]

y = df["Target"]

# =========================
# CLASS IMBALANCE
# =========================

target_counts = y.value_counts()

if 0 in target_counts and 1 in target_counts:
    scale_pos_weight = (
        target_counts[0]
        / target_counts[1]
    )
else:
    scale_pos_weight = 1

print(
    "\nScale Pos Weight:",
    round(scale_pos_weight, 2)
)

# =========================
# SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    shuffle=False
)

# =========================
# XGBOOST MODEL
# =========================

model = XGBClassifier(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.05,
    subsample=0.80,
    colsample_bytree=0.80,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss",
    random_state=42
)

# =========================
# TRAIN
# =========================

model.fit(
    X_train,
    y_train
)

# =========================
# PREDICT
# =========================

pred = model.predict(X_test)

# =========================
# METRICS
# =========================

acc = accuracy_score(
    y_test,
    pred
)

precision = precision_score(
    y_test,
    pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    pred,
    zero_division=0
)

print("\n===== XGBOOST MODEL =====")

print(
    "Accuracy :",
    round(acc * 100, 2),
    "%"
)

print(
    "Precision:",
    round(precision * 100, 2),
    "%"
)

print(
    "Recall   :",
    round(recall * 100, 2),
    "%"
)

print(
    "F1 Score :",
    round(f1 * 100, 2),
    "%"
)

# =========================
# FEATURE IMPORTANCE
# =========================

importance = pd.Series(
    model.feature_importances_,
    index=FEATURES
).sort_values(
    ascending=False
)

print("\n===== FEATURE IMPORTANCE =====")

print(importance)

# =========================
# SAVE MODEL
# =========================

joblib.dump(
    model,
    "models/xgb_model.pkl"
)

print(
    "\nModel saved -> models/xgb_model.pkl"
)

print(
    "Rows used:",
    len(df)
)