from joblib import load
import pandas as pd

model = load("models/model.pkl")

def predict_direction(features):

    X = pd.DataFrame(
        [features],
        columns=[
            "RSI",
            "EMA20",
            "EMA50",
            "MACD"
        ]
    )

    prediction = model.predict(X)[0]

    probability = model.predict_proba(X)[0]

    confidence = max(probability) * 100

    direction = "UP" if prediction == 1 else "DOWN"

    return direction, round(confidence, 2)