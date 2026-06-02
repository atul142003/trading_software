import joblib

model = joblib.load("models/xgb_model.pkl")

print("Features:", model.n_features_in_)