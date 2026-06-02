import pandas as pd
import pandas_ta as ta

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump

# Load data
df = pd.read_csv("data/reliance.csv")

# Indicators
df["EMA20"] = ta.ema(df["Close"], length=20)
df["EMA50"] = ta.ema(df["Close"], length=50)
df["RSI"] = ta.rsi(df["Close"], length=14)

macd = ta.macd(df["Close"])

df["MACD"] = macd["MACD_12_26_9"]

# Target
df["Target"] = (
    df["Close"].shift(-1) > df["Close"]
).astype(int)

# Remove missing rows
df = df.dropna()

# Features
X = df[
    [
        "RSI",
        "EMA20",
        "EMA50",
        "MACD"
    ]
]

y = df["Target"]

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# Accuracy
predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

# Save model
dump(model, "models/model.pkl")

print("Model saved successfully")