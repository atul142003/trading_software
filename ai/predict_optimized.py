"""
OPTIMIZED PREDICTION ENGINE
Uses ensemble model with advanced features for superior accuracy
Includes confidence scoring and risk management
"""

import joblib
import pandas as pd
import numpy as np


# Load models and preprocessing tools
try:
    ensemble_model = joblib.load("models/xgb_ensemble_model.pkl")
    xgb_model_opt = joblib.load("models/xgb_model_optimized.pkl")
    feature_scaler = joblib.load("models/feature_scaler.pkl")
    FEATURE_NAMES = joblib.load("models/feature_names.pkl")
    print("[OK] All models loaded successfully")
except FileNotFoundError as e:
    print(f"[ERROR] Model not found: {e}")
    print("Please run: python train_advanced_v2.py")
    exit(1)


def calculate_advanced_features(row, df=None):
    """
    Calculate all 24 advanced features for prediction
    """
    
    try:
        close = float(row.get("Close", 1))
        close_safe = max(close, 0.0001)
        
        # Basic features
        features_dict = {
            "RSI_N": float(row.get("RSI", 50)) / 100,
            "EMA20_N": float(row.get("EMA20", close)) / close_safe,
            "EMA50_N": float(row.get("EMA50", close)) / close_safe,
            "EMA200_N": float(row.get("EMA200", close)) / close_safe,
            "MACD": float(row.get("MACD", 0)),
            "MACD_SIGNAL": float(row.get("MACD_SIGNAL", 0)),
            "ATR_N": float(row.get("ATR", close*0.01)) / close_safe,
            "ADX_N": float(row.get("ADX", 20)) / 100,
            "BB_UPPER_N": float(row.get("BB_UPPER", close)) / close_safe,
            "BB_LOWER_N": float(row.get("BB_LOWER", close)) / close_safe,
            "EMA_DIFF_N": (float(row.get("EMA20", close)) - float(row.get("EMA50", close))) / close_safe,
            "Price_change": float(row.get("Price_change", 0)),
            "TF_strength": float(row.get("TF_strength", 0)),
        }
        
        # Advanced features (momentum, volatility)
        if df is not None and len(df) > 1:
            rsi_momentum = df.iloc[-1]["RSI"] - df.iloc[-2]["RSI"] if "RSI" in df.columns else 0
            macd_momentum = df.iloc[-1]["MACD"] - df.iloc[-2]["MACD"] if "MACD" in df.columns else 0
            price_velocity = df.iloc[-1].get("Price_change", 0) - (df.iloc[-2].get("Price_change", 0) if len(df) > 1 else 0)
        else:
            rsi_momentum = 0
            macd_momentum = 0
            price_velocity = 0
        
        features_dict["RSI_momentum"] = rsi_momentum
        features_dict["MACD_momentum"] = macd_momentum
        features_dict["Price_velocity"] = price_velocity
        
        # Volatility features
        close_volatility = float(row.get("Close_volatility", 0.01))
        atr_ratio = float(row.get("ATR_ratio", 0.01))
        
        features_dict["Close_volatility"] = close_volatility
        features_dict["ATR_ratio"] = atr_ratio
        
        # Trend features
        ema20 = float(row.get("EMA20", close))
        ema50 = float(row.get("EMA50", close))
        ema200 = float(row.get("EMA200", close))
        
        ema_alignment = (
            ((ema20 - ema50) > 0) * 0.5 +
            ((ema50 - ema200) > 0) * 0.5
        )
        features_dict["EMA_alignment"] = ema_alignment
        
        # Band position
        bb_upper = float(row.get("BB_UPPER", close))
        bb_lower = float(row.get("BB_LOWER", close))
        bb_range = max(bb_upper - bb_lower, 0.0001)
        bb_position = (close_safe - bb_lower) / bb_range
        bb_position = np.clip(bb_position, 0, 1)
        
        features_dict["BB_position"] = bb_position
        
        # RSI divergence
        rsi_n = float(row.get("RSI", 50)) / 100
        rsi_ema_div = (rsi_n > 0.5) - (ema20 > ema50)
        features_dict["RSI_EMA_divergence"] = rsi_ema_div
        
        # Volume features
        features_dict["Volume_ratio"] = float(row.get("Volume_ratio", 1.0))
        
        # Price patterns
        features_dict["Higher_High"] = float(row.get("Higher_High", 0))
        features_dict["Higher_Low"] = float(row.get("Higher_Low", 0))
        
        return features_dict
        
    except Exception as e:
        print(f"[ERROR] Feature calculation failed: {e}")
        return None


def predict_ensemble(features_dict):
    """
    Make prediction using ensemble model
    Returns: (signal, confidence, direction_prob)
    """
    
    try:
        # Create DataFrame with all features in correct order
        feature_vector = pd.DataFrame(
            [{name: features_dict.get(name, 0) for name in FEATURE_NAMES}]
        )
        
        # Fill any missing features with 0
        feature_vector = feature_vector.fillna(0)
        
        # Scale features
        feature_vector_scaled = feature_scaler.transform(feature_vector)
        
        # Get predictions from ensemble
        prediction = ensemble_model.predict(feature_vector_scaled)[0]
        probabilities = ensemble_model.predict_proba(feature_vector_scaled)[0]
        
        # Get individual model confidences
        xgb_prob = xgb_model_opt.predict_proba(feature_vector_scaled)[0]
        
        # Ensemble confidence (average of all model confidences)
        confidence = float(np.max(probabilities)) * 100
        
        # XGBoost specific confidence
        xgb_confidence = float(np.max(xgb_prob)) * 100
        
        # Direction
        direction = "BUY" if prediction == 1 else "SELL"
        
        return {
            "direction": direction,
            "prediction": prediction,
            "confidence": confidence,
            "xgb_confidence": xgb_confidence,
            "probabilities": {
                "sell": probabilities[0] * 100,
                "buy": probabilities[1] * 100
            },
            "model_agreement": "Strong" if abs(probabilities[0] - probabilities[1]) > 0.3 else "Weak"
        }
        
    except Exception as e:
        print(f"[ERROR] Ensemble prediction failed: {e}")
        return None


def calculate_risk_score(row):
    """
    Calculate risk score based on market volatility and trend strength
    Returns risk rating (low, medium, high)
    """
    
    try:
        atr = float(row.get("ATR", 0))
        close = float(row.get("Close", 1))
        adx = float(row.get("ADX", 20))
        tf_strength = float(row.get("TF_strength", 0))
        
        # Risk calculation
        volatility_risk = min(100, (atr / close) * 1000)  # 0-100 scale
        trend_risk = min(100, max(0, 50 - adx * 2))  # Weak trend = higher risk
        
        overall_risk = (volatility_risk * 0.6 + trend_risk * 0.4)
        
        if overall_risk < 30:
            return "LOW", overall_risk
        elif overall_risk < 60:
            return "MEDIUM", overall_risk
        else:
            return "HIGH", overall_risk
            
    except Exception as e:
        print(f"[ERROR] Risk score calculation failed: {e}")
        return "UNKNOWN", 50


def optimize_signal(row, prediction_result, df=None):
    """
    Optimize signal with risk management and filtering
    Returns: (optimized_signal, recommended_action, risk_level, confidence)
    """
    
    try:
        if prediction_result is None:
            return "HOLD", "WAIT", "UNKNOWN", 0
        
        confidence = prediction_result["confidence"]
        direction = prediction_result["direction"]
        risk_level, risk_score = calculate_risk_score(row)
        
        # Confidence thresholds based on risk
        if risk_level == "LOW":
            conf_threshold = 55
            position_size = 1.0  # 100% of capital
        elif risk_level == "MEDIUM":
            conf_threshold = 65
            position_size = 0.7  # 70% of capital
        else:  # HIGH risk
            conf_threshold = 75
            position_size = 0.4  # 40% of capital
        
        # Signal filtering
        if confidence < conf_threshold:
            signal = "HOLD"
            action = "WAIT_CONFIRMATION"
        else:
            signal = direction
            
            # Additional filters
            adx = float(row.get("ADX", 20))
            tf_strength = float(row.get("TF_strength", 0.001))
            
            # Weak trend filter
            if adx < 15 or tf_strength < 0.001:
                signal = "HOLD"
                action = "WEAK_TREND"
            else:
                action = f"TRADE_{signal}_{int(position_size*100)}%"
        
        return signal, action, risk_level, confidence
        
    except Exception as e:
        print(f"[ERROR] Signal optimization failed: {e}")
        return "HOLD", "ERROR", "UNKNOWN", 0


def make_prediction(row, df=None):
    """
    Main prediction function
    Calculates features, makes ensemble prediction, applies risk management
    
    Returns: Dictionary with all prediction details
    """
    
    features_dict = calculate_advanced_features(row, df)
    
    if features_dict is None:
        return {
            "status": "ERROR",
            "signal": "HOLD",
            "confidence": 0
        }
    
    prediction_result = predict_ensemble(features_dict)
    
    if prediction_result is None:
        return {
            "status": "ERROR",
            "signal": "HOLD",
            "confidence": 0
        }
    
    signal, action, risk_level, confidence = optimize_signal(row, prediction_result, df)
    
    return {
        "status": "OK",
        "signal": signal,
        "raw_direction": prediction_result["direction"],
        "confidence": round(confidence, 2),
        "xgb_confidence": round(prediction_result["xgb_confidence"], 2),
        "probabilities": prediction_result["probabilities"],
        "risk_level": risk_level,
        "recommended_action": action,
        "position_size": 1.0 if risk_level == "LOW" else 0.7 if risk_level == "MEDIUM" else 0.4,
        "model_agreement": prediction_result["model_agreement"]
    }


# Test function
if __name__ == "__main__":
    print("\n[TEST] Optimized Prediction Engine")
    print("="*60)
    
    # Load sample data
    try:
        df = pd.read_csv("data/reliance.csv")
        from indicators.technical import add_indicators
        
        df = add_indicators(df)
        df["EMA_diff"] = df["EMA20"] - df["EMA50"]
        df["Price_change"] = df["Close"].pct_change()
        df["Close_volatility"] = df["Close"].rolling(14).std() / df["Close"]
        df["ATR_ratio"] = df["ATR"] / df["Close"]
        df["EMA_alignment"] = (((df["EMA20"] - df["EMA50"]) > 0).astype(int) + 
                              ((df["EMA50"] - df["EMA200"]) > 0).astype(int)) / 2
        df["BB_position"] = 0.5
        df["RSI_EMA_divergence"] = 0
        df["Volume_ratio"] = 1.0
        df["Higher_High"] = 0
        df["Higher_Low"] = 0
        df["RSI_momentum"] = 0
        df["MACD_momentum"] = 0
        df["Price_velocity"] = 0
        df["TF_strength"] = abs(df["EMA20"] - df["EMA50"]) / df["Close"]
        
        latest = df.iloc[-1]
        
        result = make_prediction(latest, df)
        
        print(f"\nPrediction Result:")
        for key, value in result.items():
            print(f"  {key:20s}: {value}")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
