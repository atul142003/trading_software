"""
Comprehensive Model Accuracy Check
Evaluates XGBoost model performance with multiple metrics
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    classification_report,
)
from indicators.technical import add_indicators


def main():
    print("\n" + "=" * 70)
    print("MODEL ACCURACY ANALYSIS")
    print("=" * 70)

    print("\n[1/5] Loading data...")
    df = pd.read_csv("data/reliance.csv")
    print(f"    [OK] Loaded {len(df)} records")

    print("\n[2/5] Computing technical indicators...")
    df = add_indicators(df)
    df["EMA_diff"] = df["EMA20"] - df["EMA50"]
    if "Price_change" not in df.columns:
        df["Price_change"] = df["Close"].pct_change()

    close_safe = df["Close"].replace(0, np.nan).ffill().bfill()

    df["RSI_N"] = df["RSI"] / 100
    df["EMA20_N"] = df["EMA20"] / close_safe
    df["EMA50_N"] = df["EMA50"] / close_safe
    df["EMA200_N"] = df["EMA200"] / close_safe
    df["ATR_N"] = df["ATR"] / close_safe
    df["ADX_N"] = df["ADX"] / 100
    df["BB_UPPER_N"] = df["BB_UPPER"] / close_safe
    df["BB_LOWER_N"] = df["BB_LOWER"] / close_safe
    df["EMA_DIFF_N"] = df["EMA_diff"] / close_safe
    df["TF_strength"] = abs(df["EMA20"] - df["EMA50"]) / close_safe

    future_bars = 5
    df["Future_Return"] = df["Close"].shift(-future_bars) / df["Close"] - 1
    df["Target"] = np.where(df["Future_Return"] > (df["ATR_N"] * 0.75), 1, 0)

    df.dropna(inplace=True)
    print(f"    [OK] Indicators computed ({len(df)} valid records)")

    print("\n[3/5] Preparing features...")

    FEATURES = [
        "RSI_N", "EMA20_N", "EMA50_N", "EMA200_N",
        "MACD", "MACD_SIGNAL", "ATR_N", "ADX_N",
        "BB_UPPER_N", "BB_LOWER_N", "EMA_DIFF_N",
        "Price_change", "TF_strength",
    ]

    X = df[FEATURES]
    y = df["Target"]

    print(f"    [OK] Features: {len(FEATURES)}")
    print(f"    [OK] Training samples: {len(X)}")
    print(f"    [OK] Target distribution: {dict(y.value_counts())}")
    print(f"    [OK] Positive class ratio: {y.mean() * 100:.2f}%")

    print("\n[4/5] Loading trained model...")

    try:
        model = joblib.load("models/xgb_model.pkl")
        print("    [OK] Model loaded successfully")
    except FileNotFoundError:
        print("    [!] Model file not found. Training new model...")
        from xgboost import XGBClassifier

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, shuffle=False
        )

        target_counts = y.value_counts()
        scale_pos_weight = (
            target_counts[0] / target_counts[1] if 1 in target_counts else 1
        )

        model = XGBClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.80,
            colsample_bytree=0.80,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )

        model.fit(X_train, y_train)
        joblib.dump(model, "models/xgb_model.pkl")
        print("    [OK] New model trained and saved")

    print("\n[5/5] Evaluating model performance...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, shuffle=False
    )

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_pred_proba)

    cm = confusion_matrix(y_test, y_pred)

    print("    [OK] Metrics calculated")

    print("\n[CROSS-VALIDATION] 5-Fold CV Score...")

    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
    cv_f1 = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")

    print(f"    CV Accuracy: {cv_scores.mean() * 100:.2f}% (+/-{cv_scores.std() * 100:.2f}%)")
    print(f"    CV F1-Score: {cv_f1.mean() * 100:.2f}% (+/-{cv_f1.std() * 100:.2f}%)")

    print("\n" + "=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)

    print(f"\nTest Set Accuracy: {accuracy * 100:.2f}%")
    print(f"   Precision (Buy):  {precision * 100:.2f}%")
    print(f"   Recall (Buy):     {recall * 100:.2f}%")
    print(f"   F1-Score:         {f1 * 100:.2f}%")
    print(f"   ROC-AUC:          {roc_auc * 100:.2f}%")

    print("\nConfusion Matrix:")
    print(f"   True Negatives (Correct SELL):  {cm[0, 0]}")
    print(f"   False Positives (Wrong BUY):    {cm[0, 1]}")
    print(f"   False Negatives (Wrong SELL):   {cm[1, 0]}")
    print(f"   True Positives (Correct BUY):   {cm[1, 1]}")

    print("\nModel Reliability:")
    specificity = cm[0, 0] / (cm[0, 0] + cm[0, 1]) if (cm[0, 0] + cm[0, 1]) > 0 else 0
    sensitivity = cm[1, 1] / (cm[1, 1] + cm[1, 0]) if (cm[1, 1] + cm[1, 0]) > 0 else 0
    print(f"   Specificity (Sell Accuracy):    {specificity * 100:.2f}%")
    print(f"   Sensitivity (Buy Accuracy):     {sensitivity * 100:.2f}%")

    print("\nFeature Importance:")
    importance = model.get_booster().get_score(importance_type="weight")
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for idx, (feature, score) in enumerate(sorted_importance[:8], 1):
        print(f"   {idx}. {feature}: {score}")

    print("\n" + "=" * 70)
    print("DETAILED CLASSIFICATION REPORT")
    print("=" * 70)
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["SELL (0)", "BUY (1)"],
            zero_division=0,
        )
    )

    print("=" * 70)
    print("SIMPLE BACKTEST SIMULATION")
    print("=" * 70)

    backtest_df = df.copy()
    backtest_df["pred"] = model.predict(X)
    backtest_df["pred_proba"] = model.predict_proba(X)[:, 1]
    backtest_df["returns"] = backtest_df["Close"].pct_change()
    backtest_df["strategy_returns"] = np.where(
        backtest_df["pred"].shift(1) == 1,
        backtest_df["returns"],
        -backtest_df["returns"],
    )

    total_return = backtest_df["strategy_returns"].dropna().sum() * 100
    buy_and_hold = backtest_df["returns"].dropna().sum() * 100
    win_rate = (
        (backtest_df["strategy_returns"].dropna() > 0).sum()
        / len(backtest_df["strategy_returns"].dropna())
        * 100
    )

    print(f"\nStrategy Returns:    {total_return:+.2f}%")
    print(f"Buy & Hold Returns:  {buy_and_hold:+.2f}%")
    print(f"Win Rate:            {win_rate:.2f}%")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if accuracy > 0.60:
        rating = "GOOD"
    elif accuracy > 0.55:
        rating = "FAIR"
    else:
        rating = "POOR"

    print(f"\nModel Rating: {rating}")
    print(f"Primary Metric: Accuracy = {accuracy * 100:.2f}%")
    print(
        f"Recommendation: {'Use with confidence' if accuracy > 0.60 else 'Needs improvement'}"
    )
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
