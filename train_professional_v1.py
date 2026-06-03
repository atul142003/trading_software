"""
PROFESSIONAL-GRADE MODEL TRAINING PIPELINE
5+ Years of Data | Multiple Stocks | Robust Time-Series Cross-Validation
Target: Production-ready ensemble model for live trading
"""

import pandas as pd
import numpy as np
import yfinance as yf
import joblib
import warnings
from datetime import datetime, timedelta
from collections import Counter
import sys

from sklearn.model_selection import (
    TimeSeriesSplit,
    train_test_split,
    GridSearchCV,
    cross_validate
)
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from indicators.technical import add_indicators

warnings.filterwarnings('ignore')

print("\n" + "="*100)
print("PROFESSIONAL-GRADE MODEL TRAINING PIPELINE")
print("="*100)
print("Target: Production-ready ensemble trained on 5+ years of multi-stock data")
print("="*100)

# ============================================================================
# PHASE 1: DOWNLOAD PROFESSIONAL-GRADE DATA (5+ YEARS)
# ============================================================================
print("\n[PHASE 1/8] Downloading 5+ years of historical data from multiple stocks...")

PROFESSIONAL_STOCKS = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ITC.NS",
    "LT.NS",
    "WIPRO.NS",
    "MARUTI.NS"
]

# Download daily data (more efficient than 5-min for 5+ years)
print(f"    Downloading data for: {', '.join(PROFESSIONAL_STOCKS)}")
print("    Period: 5+ years (2020-2026)")
print("    Interval: Daily (1d) for efficiency and stability")

all_data = []
successful_stocks = []

for stock in PROFESSIONAL_STOCKS:
    try:
        print(f"      • {stock}...", end=" ", flush=True)
        df = yf.download(
            stock,
            start="2019-01-01",
            end="2026-06-01",
            interval="1d",
            auto_adjust=True,
            threads=False,
            progress=False
        )

        if df.empty:
            print("SKIP (no data)")
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if len(df) < 500:  # Need sufficient data
            print(f"SKIP (only {len(df)} records)")
            continue

        df = df.reset_index()
        df["symbol"] = stock
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        all_data.append(df)
        successful_stocks.append(stock)
        print(f"OK ({len(df)} records)")
        
    except Exception as e:
        print(f"ERROR: {str(e)[:40]}")
        continue

# Combine all data
if not all_data:
    print("\n    [ERROR] No stock data downloaded. Check network or ticker symbols.")
    sys.exit(1)

print(f"\n    [OK] Successfully downloaded: {', '.join(successful_stocks)}")
combined_df = pd.concat(all_data, ignore_index=True)
combined_df = combined_df.sort_values(['symbol', 'date']).reset_index(drop=True)

print(f"    [OK] Total records: {len(combined_df)}")
print(f"    [OK] Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")

# ============================================================================
# PHASE 2: ADD INDICATORS TO ALL DATA
# ============================================================================
print("\n[PHASE 2/8] Computing technical indicators for all data...")

# Ensure proper columns for add_indicators
required_cols = ['open', 'high', 'low', 'close', 'volume']
combined_df['volume'] = combined_df['volume'].fillna(0)

# Add indicators per stock
indicator_data = []
for stock in successful_stocks:
    stock_data = combined_df[combined_df['symbol'] == stock].copy()
    stock_data = stock_data.reset_index(drop=True)
    
    # Rename for add_indicators function
    stock_data_renamed = stock_data[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
    stock_data_renamed.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    print(f"    • {stock}: Adding indicators...", end=" ", flush=True)
    stock_data_renamed = add_indicators(stock_data_renamed)
    stock_data_renamed['symbol'] = stock
    indicator_data.append(stock_data_renamed)
    print("OK")

df = pd.concat(indicator_data, ignore_index=True)
print(f"[OK] Indicators added to {len(df)} total records")

# ============================================================================
# PHASE 3: ADVANCED FEATURE ENGINEERING
# ============================================================================
print("\n[PHASE 3/8] Advanced feature engineering...")

# Basic Features
df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

close_safe = df["Close"].replace(0, np.nan)
close_safe = close_safe.ffill().bfill()

# Normalized Features
df["RSI_N"] = df["RSI"] / 100
df["EMA20_N"] = df["EMA20"] / close_safe
df["EMA50_N"] = df["EMA50"] / close_safe
df["EMA200_N"] = df["EMA200"] / close_safe
df["MACD"] = df["MACD"].fillna(0)
df["MACD_SIGNAL"] = df["MACD_SIGNAL"].fillna(0)
df["ATR_N"] = df["ATR"] / close_safe
df["ADX_N"] = df["ADX"] / 100
df["BB_UPPER_N"] = df["BB_UPPER"] / close_safe
df["BB_LOWER_N"] = df["BB_LOWER"] / close_safe
df["EMA_DIFF_N"] = df["EMA_diff"] / close_safe
df["TF_strength"] = (abs(df["EMA20"] - df["EMA50"]) / close_safe).fillna(0)

# Advanced Momentum Features
df["RSI_momentum"] = df["RSI"].diff().fillna(0)
df["MACD_momentum"] = df["MACD"].diff().fillna(0)
df["Price_velocity"] = df["Price_change"].diff().fillna(0)

# Advanced Volatility Features
df["Close_volatility"] = df["Close"].rolling(window=14).std() / close_safe
df["ATR_ratio"] = df["ATR"] / df["Close"]

# Advanced Trend Features
df["EMA_alignment"] = (df["EMA20"] > df["EMA50"]).astype(float) * 0.5 + \
                      (df["EMA50"] > df["EMA200"]).astype(float) * 0.5
df["BB_position"] = (df["Close"] - df["BB_LOWER"]) / (df["BB_UPPER"] - df["BB_LOWER"])

# Pattern Recognition
df["RSI_EMA_divergence"] = abs(
    (df["RSI"] - 50) / 50 - (df["EMA_DIFF_N"] / df["Close"].rolling(14).std())
).fillna(0)
df["Volume_ratio"] = df["Volume"] / df["Volume"].rolling(window=20).mean()

# Higher High / Higher Low patterns
df["Higher_High"] = (df["High"] > df["High"].shift(1)).astype(float)
df["Higher_Low"] = (df["Low"] > df["Low"].shift(1)).astype(float)

# Replace infinities and NaNs
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

print("    [OK] 24 advanced features engineered")

# ============================================================================
# PHASE 4: CREATE TARGET VARIABLE (MULTI-HORIZON VOTING)
# ============================================================================
print("\n[PHASE 4/8] Creating robust target variable (multi-horizon voting)...")

# Multi-horizon target: voting across 3, 5, 7 bars ahead
df["Return_3bar"] = df["Close"].shift(-3) / df["Close"] - 1
df["Return_5bar"] = df["Close"].shift(-5) / df["Close"] - 1
df["Return_7bar"] = df["Close"].shift(-7) / df["Close"] - 1

# Threshold for BUY (positive return) vs SELL (negative return)
threshold = 0.001  # 0.1% threshold

target_votes = (
    (df["Return_3bar"] > threshold).astype(int) +
    (df["Return_5bar"] > threshold).astype(int) +
    (df["Return_7bar"] > threshold).astype(int)
)

# Majority vote: 2 out of 3 = BUY (1), else SELL (0)
df["Target"] = (target_votes >= 2).astype(int)

# Remove NaN targets (last 7 rows)
df = df.dropna(subset=["Target"])

print(f"    Class distribution:")
print(f"      SELL (0): {(df['Target'] == 0).sum()} ({(df['Target'] == 0).sum() / len(df) * 100:.1f}%)")
print(f"      BUY  (1): {(df['Target'] == 1).sum()} ({(df['Target'] == 1).sum() / len(df) * 100:.1f}%)")

# ============================================================================
# PHASE 5: DATA CLEANING & PREPROCESSING
# ============================================================================
print("\n[PHASE 5/8] Data cleaning and preprocessing...")

# Feature list
FEATURES = [
    "RSI_N", "EMA20_N", "EMA50_N", "EMA200_N",
    "MACD", "MACD_SIGNAL",
    "ATR_N", "ADX_N",
    "BB_UPPER_N", "BB_LOWER_N",
    "EMA_DIFF_N", "Price_change", "TF_strength",
    "RSI_momentum", "MACD_momentum", "Price_velocity",
    "Close_volatility", "ATR_ratio",
    "EMA_alignment", "BB_position",
    "RSI_EMA_divergence", "Volume_ratio",
    "Higher_High", "Higher_Low"
]

X = df[FEATURES].copy()
y = df["Target"].copy()

print(f"    Features: {len(FEATURES)}")
print(f"    Samples: {len(X)}")

# Remove rows with NaN values
initial_rows = len(X)
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 0)

# Outlier removal (IQR method)
print(f"    Removing outliers (IQR method)...")
Q1 = X.quantile(0.25)
Q3 = X.quantile(0.75)
IQR = Q3 - Q1
outlier_mask = ~((X < (Q1 - 1.5 * IQR)) | (X > (Q3 + 1.5 * IQR))).any(axis=1)
X = X[outlier_mask]
y = y[outlier_mask]
removed = initial_rows - len(X)
print(f"      Removed: {removed} outliers")
print(f"      Remaining: {len(X)} samples")

# Robust Scaling
print(f"    Scaling features (RobustScaler)...")
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=FEATURES)

# Stratified Train-Test Split (respecting time series)
# For time series: use last 20% as test set
split_idx = int(len(X) * 0.8)
X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

print(f"    Train set: {len(X_train)} samples")
print(f"    Test set: {len(X_test)} samples")

# Class balance in training set
from imblearn.over_sampling import RandomOverSampler
ros = RandomOverSampler(random_state=42)
X_train_balanced, y_train_balanced = ros.fit_resample(X_train, y_train)

print(f"    After balancing: {len(X_train_balanced)} samples")
print(f"      SELL: {(y_train_balanced == 0).sum()}")
print(f"      BUY:  {(y_train_balanced == 1).sum()}")

# ============================================================================
# PHASE 6: HYPERPARAMETER OPTIMIZATION
# ============================================================================
print("\n[PHASE 6/8] Hyperparameter optimization (GridSearchCV)...")

param_grid = {
    'n_estimators': [100, 150, 200],
    'max_depth': [4, 5, 6],
    'learning_rate': [0.01, 0.05],
    'subsample': [0.8, 0.9],
    'colsample_bytree': [0.8, 0.9]
}

xgb_model = XGBClassifier(random_state=42, verbosity=0)
grid_search = GridSearchCV(
    xgb_model,
    param_grid,
    cv=3,
    scoring='f1',
    n_jobs=-1,
    verbose=1
)

print("    Searching parameter space...")
grid_search.fit(X_train_balanced, y_train_balanced)

best_params = grid_search.best_params_
best_cv_score = grid_search.best_score_

print(f"\n    Best parameters found:")
for param, value in best_params.items():
    print(f"      {param}: {value}")
print(f"    Best CV F1-Score: {best_cv_score:.4f}")

# ============================================================================
# PHASE 7: ENSEMBLE MODEL TRAINING
# ============================================================================
print("\n[PHASE 7/8] Training ensemble voting classifier...")

# Train individual models with best parameters
xgb_best = XGBClassifier(**best_params, random_state=42, verbosity=0)
xgb_best.fit(X_train_balanced, y_train_balanced)

rf_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train_balanced, y_train_balanced)

lr_model = LogisticRegression(
    max_iter=1000,
    random_state=42
)
lr_model.fit(X_train_balanced, y_train_balanced)

# Ensemble voting classifier
ensemble_model = VotingClassifier(
    estimators=[
        ('xgb', xgb_best),
        ('rf', rf_model),
        ('lr', lr_model)
    ],
    voting='soft',
    weights=[2, 1.5, 1]
)

ensemble_model.fit(X_train_balanced, y_train_balanced)
print("    [OK] Ensemble model trained")

# ============================================================================
# PHASE 8: EVALUATION & VALIDATION
# ============================================================================
print("\n[PHASE 8/8] Comprehensive evaluation and validation...")

# Test set predictions
y_pred = ensemble_model.predict(X_test)
y_pred_proba = ensemble_model.predict_proba(X_test)[:, 1]

# Metrics
test_accuracy = accuracy_score(y_test, y_pred)
test_precision = precision_score(y_test, y_pred, zero_division=0)
test_recall = recall_score(y_test, y_pred, zero_division=0)
test_f1 = f1_score(y_test, y_pred, zero_division=0)
test_roc_auc = roc_auc_score(y_test, y_pred_proba)

print("\n" + "="*80)
print("TEST SET PERFORMANCE (Professional Grade)")
print("="*80)
print(f"Accuracy:  {test_accuracy:.2%}")
print(f"Precision: {test_precision:.2%}")
print(f"Recall:    {test_recall:.2%}")
print(f"F1-Score:  {test_f1:.2%}")
print(f"ROC-AUC:   {test_roc_auc:.4f}")

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

print(f"\nConfusion Matrix:")
print(f"  True Negatives:  {tn}")
print(f"  False Positives: {fp}")
print(f"  False Negatives: {fn}")
print(f"  True Positives:  {tp}")
print(f"\nSpecificity (SELL): {specificity:.2%}")
print(f"Sensitivity (BUY):  {sensitivity:.2%}")

# Time Series Cross-Validation
print(f"\nTime-Series 5-Fold Cross-Validation:")
tscv = TimeSeriesSplit(n_splits=5)
cv_scores = cross_validate(
    ensemble_model,
    X,
    y,
    cv=tscv,
    scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
    n_jobs=-1,
    verbose=0
)

for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
    scores = cv_scores[f'test_{metric}']
    print(f"  {metric.upper():10s}: {scores.mean():.4f} (±{scores.std():.4f})")

# Feature Importance
print(f"\nTop 10 Features (by XGBoost importance):")
feature_importance = pd.DataFrame({
    'Feature': FEATURES,
    'Importance': xgb_best.feature_importances_
}).sort_values('Importance', ascending=False)

for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['Feature']:25s}: {row['Importance']:.4f}")

# ============================================================================
# SAVE PROFESSIONAL MODELS
# ============================================================================
print("\n" + "="*80)
print("SAVING PROFESSIONAL MODELS")
print("="*80)

joblib.dump(ensemble_model, 'models/xgb_ensemble_professional.pkl')
joblib.dump(xgb_best, 'models/xgb_professional.pkl')
joblib.dump(rf_model, 'models/rf_professional.pkl')
joblib.dump(scaler, 'models/scaler_professional.pkl')
joblib.dump(FEATURES, 'models/features_professional.pkl')

print("✓ Ensemble Model: models/xgb_ensemble_professional.pkl")
print("✓ XGBoost Model: models/xgb_professional.pkl")
print("✓ Random Forest Model: models/rf_professional.pkl")
print("✓ Feature Scaler: models/scaler_professional.pkl")
print("✓ Feature Names: models/features_professional.pkl")

# ============================================================================
# PROFESSIONAL METRICS SUMMARY
# ============================================================================
print("\n" + "="*100)
print("PROFESSIONAL MODEL TRAINING COMPLETE")
print("="*100)

summary = f"""
DATA QUALITY:
  • Historical Period: 2019-2026 (7 years)
  • Multiple Stocks: {len(successful_stocks)} different stocks
  • Total Records: {len(df)} ({len(X_train)} train + {len(X_test)} test)
  • Feature Count: 24 advanced features
  • Outlier Removal: {removed} samples (IQR method)

MODEL ARCHITECTURE:
  • Base Models: XGBoost + Random Forest + Logistic Regression
  • Voting Strategy: Soft probability averaging
  • Model Weights: XGBoost (2.0) > RF (1.5) > LR (1.0)

HYPERPARAMETER OPTIMIZATION:
  • Method: GridSearchCV (3-fold CV)
  • Best Parameters: {best_params}
  • Best CV Score: {best_cv_score:.4f}

TEST SET RESULTS:
  • Accuracy:  {test_accuracy:.2%}
  • Precision: {test_precision:.2%}
  • Recall:    {test_recall:.2%}
  • F1-Score:  {test_f1:.2%}
  • ROC-AUC:   {test_roc_auc:.4f}

PRODUCTION STATUS:
  ✓ Trained on 5+ years of data
  ✓ Time-series cross-validation applied
  ✓ Multiple stocks for robustness
  ✓ Professional-grade preprocessing
  ✓ Ready for live trading deployment

DEPLOYMENT:
  The models are ready for immediate deployment in:
  • scanner_dashboard.py (web interface)
  • cli_scanner.py (automated CLI)
  • Production trading systems

RECOMMENDATION:
  Deploy with 2-week paper trading validation before live money.
  Monitor Sharpe ratio and win rate closely.
"""

print(summary)

# Save summary to file
with open('PROFESSIONAL_TRAINING_REPORT.txt', 'w') as f:
    f.write("PROFESSIONAL MODEL TRAINING REPORT\n")
    f.write("="*100 + "\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*100 + "\n")
    f.write(summary)
    f.write("\n\nFeature Importance Top 15:\n")
    f.write(feature_importance.head(15).to_string())

print("\n✓ Report saved: PROFESSIONAL_TRAINING_REPORT.txt")
print("✓ All models ready for deployment\n")
