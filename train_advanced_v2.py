"""
ADVANCED TRADING MODEL - BUSINESS LEVEL OPTIMIZATION
Implements ensemble methods, hyperparameter tuning, and advanced feature engineering
Target: Improve Accuracy to 65%+, Precision to 55%+, F1-Score to 60%+
"""

import pandas as pd
import numpy as np
import joblib
import warnings
from datetime import datetime

from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    StratifiedKFold,
    cross_validate
)
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from indicators.technical import add_indicators

warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("ADVANCED XGBOOST + ENSEMBLE MODEL TRAINING")
print("="*80)

# PHASE 1: LOAD & ENHANCE DATA
print("\n[PHASE 1/5] Loading and enhancing data...")

df = pd.read_csv("data/reliance.csv")
df = add_indicators(df)

print(f"    [OK] Loaded {len(df)} records")

# ADVANCED FEATURE ENGINEERING
print("\n[PHASE 2/5] Advanced feature engineering...")

df["EMA_diff"] = df["EMA20"] - df["EMA50"]
df["Price_change"] = df["Close"].pct_change()

close_safe = df["Close"].replace(0, np.nan)
close_safe = close_safe.ffill()  # Forward fill instead of bfill

# Normalized Features
df["RSI_N"] = df["RSI"] / 100
df["EMA20_N"] = df["EMA20"] / close_safe
df["EMA50_N"] = df["EMA50"] / close_safe
df["EMA200_N"] = df["EMA200"] / close_safe
df["ATR_N"] = df["ATR"] / close_safe
df["ADX_N"] = df["ADX"] / 100
df["BB_UPPER_N"] = df["BB_UPPER"] / close_safe
df["BB_LOWER_N"] = df["BB_LOWER"] / close_safe
df["EMA_DIFF_N"] = df["EMA_diff"] / close_safe
df["TF_strength"] = (abs(df["EMA20"] - df["EMA50"]) / close_safe).fillna(0)

# NEW ADVANCED FEATURES
print("    Adding advanced features...")

# Momentum Features
df["RSI_momentum"] = df["RSI"].diff().fillna(0)
df["MACD_momentum"] = df["MACD"].diff().fillna(0)
df["Price_velocity"] = df["Price_change"].diff().fillna(0)

# Volatility Features
df["Close_volatility"] = df["Close"].rolling(window=14).std() / close_safe
df["ATR_ratio"] = df["ATR"] / df["Close"]

# Trend Strength Features
df["EMA_alignment"] = (
    ((df["EMA20"] - df["EMA50"]) > 0).astype(int) +
    ((df["EMA50"] - df["EMA200"]) > 0).astype(int)
) / 2

# Band Position Features
df["BB_position"] = (close_safe - df["BB_LOWER"]) / (df["BB_UPPER"] - df["BB_LOWER"])
df["BB_position"] = df["BB_position"].clip(0, 1).fillna(0.5)

# RSI divergence
df["RSI_EMA_divergence"] = (
    (df["RSI_N"] > 0.5).astype(int) - 
    ((df["EMA20"] > df["EMA50"]).astype(int))
)

# Volume features
if "Volume" in df.columns:
    df["Volume_MA"] = df["Volume"].rolling(window=20).mean()
    df["Volume_ratio"] = df["Volume"] / (df["Volume_MA"] + 1)
    df["Volume_ratio"] = df["Volume_ratio"].fillna(1).clip(0, 5)
else:
    df["Volume_ratio"] = 1.0

# Price patterns
df["Higher_High"] = (df["Close"] > df["Close"].shift(1)).astype(int)
df["Higher_Low"] = df["Close"].rolling(2).min() > df["Close"].rolling(2).min().shift(1)
df["Higher_Low"] = df["Higher_Low"].fillna(0).astype(int)

# IMPROVED TARGET
print("    Optimizing target variable...")

future_bars_list = [3, 5, 7]
returns_list = []

for fb in future_bars_list:
    future_return = (df["Close"].shift(-fb) / df["Close"] - 1).fillna(0)
    atr_threshold = df["ATR"] / df["Close"]
    returns_list.append(future_return > (atr_threshold * 0.75))

df["Target"] = (returns_list[0].astype(int) + 
                returns_list[1].astype(int) + 
                returns_list[2].astype(int)) >= 2
df["Target"] = df["Target"].astype(int)

df = df.dropna(subset=["Target"])
df = df.replace([np.inf, -np.inf], np.nan).dropna()

print(f"    [OK] Target distribution: {dict(df['Target'].value_counts())}")
print(f"    [OK] Buy ratio: {df['Target'].mean()*100:.2f}%")

# FEATURE SELECTION
print("    Selecting features...")

FEATURES = [
    "RSI_N", "EMA20_N", "EMA50_N", "EMA200_N",
    "MACD", "MACD_SIGNAL",
    "ATR_N", "ADX_N",
    "BB_UPPER_N", "BB_LOWER_N",
    "EMA_DIFF_N", "Price_change",
    "TF_strength",
    "RSI_momentum", "MACD_momentum", "Price_velocity",
    "Close_volatility", "ATR_ratio",
    "EMA_alignment", "BB_position",
    "RSI_EMA_divergence", "Volume_ratio",
    "Higher_High", "Higher_Low"
]

X = df[FEATURES].copy()
y = df["Target"].copy()

print(f"    [OK] Total features: {len(FEATURES)}")
print(f"    [OK] Training samples: {len(X)}")

# DATA PREPROCESSING
print("\n[PHASE 3/5] Data preprocessing...")

X = X.fillna(X.median())

# Outlier removal
Q1 = X.quantile(0.25)
Q3 = X.quantile(0.75)
IQR = Q3 - Q1
outlier_mask = ~((X < (Q1 - 1.5*IQR)) | (X > (Q3 + 1.5*IQR))).any(axis=1)
X = X[outlier_mask]
y = y[outlier_mask]

print(f"    [OK] Outliers removed: {(~outlier_mask).sum()} rows")
print(f"    [OK] Remaining samples: {len(X)}")

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"    [OK] Train set: {len(X_train)} | Test set: {len(X_test)}")

# Scaling
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"    [OK] Features scaled with RobustScaler")

# Class balancing via duplication (on scaled data)
from collections import Counter
train_counts = Counter(y_train)
majority_count = max(train_counts.values())

minority_indices_train = np.where(y_train == y_train.value_counts().idxmin())[0]
majority_indices_train = np.where(y_train == y_train.value_counts().idxmax())[0]

# Oversample minority class to match majority
oversample_indices = np.random.choice(
    minority_indices_train,
    len(majority_indices_train),
    replace=True
)

balanced_train_indices = np.concatenate([majority_indices_train, oversample_indices])
np.random.shuffle(balanced_train_indices)

X_train_balanced = X_train_scaled[balanced_train_indices]
y_train_balanced = y_train.iloc[balanced_train_indices].values

print(f"    [OK] Class balancing applied: {dict(zip(*np.unique(y_train_balanced, return_counts=True)))}")

# HYPERPARAMETER OPTIMIZATION
print("\n[PHASE 4/5] Hyperparameter optimization (GridSearchCV)...")

target_counts = pd.Series(y_train_balanced).value_counts()
scale_pos_weight = (target_counts[0] / target_counts[1]) if 1 in target_counts else 1

print("    Searching XGBoost parameters...")

xgb_model = XGBClassifier(
    scale_pos_weight=scale_pos_weight,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1,
    verbosity=0
)

xgb_grid = GridSearchCV(
    xgb_model,
    param_grid={
        'n_estimators': [150],
        'max_depth': [4, 5],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8, 0.9],
        'colsample_bytree': [0.8, 0.9]
    },
    cv=3,
    scoring='f1',
    n_jobs=-1,
    verbose=0
)

xgb_grid.fit(X_train_balanced, y_train_balanced)

print(f"    [OK] Best XGBoost params: {xgb_grid.best_params_}")
print(f"    [OK] Best CV F1 score: {xgb_grid.best_score_:.4f}")

xgb_best = xgb_grid.best_estimator_

# ENSEMBLE MODEL
print("\n[PHASE 5/5] Building ensemble model...")

rf_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=8,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

lr_model = LogisticRegression(
    max_iter=1000,
    random_state=42
)

voting_clf = VotingClassifier(
    estimators=[
        ('xgb', xgb_best),
        ('rf', rf_model),
        ('lr', lr_model)
    ],
    voting='soft',
    weights=[2, 1.5, 1]
)

print("    Training ensemble: XGBoost + RandomForest + LogisticRegression")

voting_clf.fit(X_train_balanced, y_train_balanced)

# EVALUATION
print("\n" + "="*80)
print("PERFORMANCE METRICS")
print("="*80)

y_pred = voting_clf.predict(X_test_scaled)
y_pred_proba = voting_clf.predict_proba(X_test_scaled)[:, 1]

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, zero_division=0)
rec = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, y_pred_proba)
cm = confusion_matrix(y_test, y_pred)

print(f"\nTEST SET PERFORMANCE")
print(f"    Accuracy:  {acc*100:.2f}%     (Target: >65%)")
print(f"    Precision: {prec*100:.2f}%     (Target: >55%)")
print(f"    Recall:    {rec*100:.2f}%     (Target: >65%)")
print(f"    F1-Score:  {f1*100:.2f}%     (Target: >60%)")
print(f"    ROC-AUC:   {roc_auc*100:.2f}%")

# Cross-validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_validate(
    voting_clf,
    X_train_balanced,
    y_train_balanced,
    cv=skf,
    scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
    n_jobs=-1
)

print(f"\nCROSS-VALIDATION (5-Fold)")
print(f"    Accuracy:  {cv_scores['test_accuracy'].mean()*100:.2f}% +/- {cv_scores['test_accuracy'].std()*100:.2f}%")
print(f"    Precision: {cv_scores['test_precision'].mean()*100:.2f}% +/- {cv_scores['test_precision'].std()*100:.2f}%")
print(f"    Recall:    {cv_scores['test_recall'].mean()*100:.2f}% +/- {cv_scores['test_recall'].std()*100:.2f}%")
print(f"    F1-Score:  {cv_scores['test_f1'].mean()*100:.2f}% +/- {cv_scores['test_f1'].std()*100:.2f}%")
print(f"    ROC-AUC:   {cv_scores['test_roc_auc'].mean()*100:.2f}% +/- {cv_scores['test_roc_auc'].std()*100:.2f}%")

# Confusion Matrix
print(f"\nCONFUSION MATRIX")
tn, fp, fn, tp = cm.ravel()
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0

print(f"    True Negatives:  {tn}  (Correct SELL)")
print(f"    False Positives: {fp}  (Wrong BUY)")
print(f"    False Negatives: {fn}  (Wrong SELL)")
print(f"    True Positives:  {tp}  (Correct BUY)")
print(f"    Specificity:     {specificity*100:.2f}% (Sell accuracy)")
print(f"    Sensitivity:     {sensitivity*100:.2f}% (Buy accuracy)")

# Feature Importance
print(f"\nENSEMBLE FEATURE IMPORTANCE")
feature_importance_xgb = pd.DataFrame({
    'feature': FEATURES,
    'importance': xgb_best.feature_importances_
}).sort_values('importance', ascending=False).head(10)

print(f"    Top 10 features (XGBoost):")
for idx, row in feature_importance_xgb.iterrows():
    print(f"      {row['feature']:20s}: {row['importance']:.2f}")

# SAVE MODELS
print("\n" + "="*80)
print("SAVING MODELS")
print("="*80)

joblib.dump(voting_clf, "models/xgb_ensemble_model.pkl")
print(f"    [OK] Ensemble model saved -> models/xgb_ensemble_model.pkl")

joblib.dump(xgb_best, "models/xgb_model_optimized.pkl")
joblib.dump(rf_model, "models/rf_model.pkl")
print(f"    [OK] Individual models saved")

joblib.dump(scaler, "models/feature_scaler.pkl")
print(f"    [OK] Feature scaler saved -> models/feature_scaler.pkl")

joblib.dump(FEATURES, "models/feature_names.pkl")
print(f"    [OK] Feature metadata saved")

# SUMMARY REPORT
print("\n" + "="*80)
print("OPTIMIZATION SUMMARY")
print("="*80)

improvements = {
    'Accuracy': (acc - 0.5593) * 100,
    'Precision': (prec - 0.3226) * 100,
    'Recall': (rec - 0.6667) * 100,
    'F1-Score': (f1 - 0.4348) * 100,
}

print("\nIMPROVEMENTS vs BASELINE")
for metric, improvement in improvements.items():
    direction = "UP" if improvement > 0 else "DOWN"
    print(f"    {metric:12s}: {direction} {abs(improvement):+.2f}%")

print(f"\nACHIEVEMENTS")
print(f"    [+] Advanced feature engineering (24 features)")
print(f"    [+] Hyperparameter optimization via GridSearchCV")
print(f"    [+] Class balancing via oversampling")
print(f"    [+] Ensemble voting classifier (3 models)")
print(f"    [+] Stratified K-Fold cross-validation")
print(f"    [+] Robust scaling for outlier resistance")
print(f"    [+] Multi-horizon target voting")
print(f"    [+] Stratified train-test split")

print(f"\n{'='*80}\n")

# Save report
with open("models/training_report_advanced.txt", "w") as f:
    f.write(f"""
ADVANCED MODEL TRAINING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PERFORMANCE METRICS:
  Accuracy:  {acc*100:.2f}%
  Precision: {prec*100:.2f}%
  Recall:    {rec*100:.2f}%
  F1-Score:  {f1*100:.2f}%
  ROC-AUC:   {roc_auc*100:.2f}%

CROSS-VALIDATION:
  Accuracy:  {cv_scores['test_accuracy'].mean()*100:.2f}% +/- {cv_scores['test_accuracy'].std()*100:.2f}%
  Precision: {cv_scores['test_precision'].mean()*100:.2f}% +/- {cv_scores['test_precision'].std()*100:.2f}%
  F1-Score:  {cv_scores['test_f1'].mean()*100:.2f}% +/- {cv_scores['test_f1'].std()*100:.2f}%

IMPROVEMENTS:
  Accuracy:  {improvements['Accuracy']:+.2f}%
  Precision: {improvements['Precision']:+.2f}%
  Recall:    {improvements['Recall']:+.2f}%
  F1-Score:  {improvements['F1-Score']:+.2f}%

FEATURES: {len(FEATURES)} total
TRAINING SAMPLES: {len(X_train_balanced)}
TEST SAMPLES: {len(X_test)}
""")

print("Report saved -> models/training_report_advanced.txt")
