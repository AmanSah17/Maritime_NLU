import sqlite3
import pickle
import numpy as np

# Check database schema
print("=" * 80)
print("DATABASE SCHEMA")
print("=" * 80)
conn = sqlite3.connect('backend/nlu_chatbot/maritime_sample_0104.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(vessel_data)")
cols = cursor.fetchall()
print('Database Columns:')
for i, col in enumerate(cols):
    print(f'{i+1}. {col[1]} ({col[2]})')
conn.close()

# Check model artifacts
print("\n" + "=" * 80)
print("MODEL ARTIFACTS")
print("=" * 80)

model_path = "F:\\PyTorch_GPU\\maritime_vessel_forecasting\\Multi_vessel_forecasting\\results\\xgboost_advanced_50_vessels"

# Load scaler
print("\nLoading StandardScaler...")
with open(f"{model_path}\\scaler.pkl", 'rb') as f:
    scaler = pickle.load(f)
print(f"✅ Scaler loaded")
print(f"   - n_features_in_: {scaler.n_features_in_}")
print(f"   - Expected input shape: (n_samples, {scaler.n_features_in_})")

# Load PCA
print("\nLoading PCA...")
with open(f"{model_path}\\pca.pkl", 'rb') as f:
    pca = pickle.load(f)
print(f"✅ PCA loaded")
print(f"   - n_features_in_: {pca.n_features_in_}")
print(f"   - n_components_: {pca.n_components_}")
print(f"   - Expected input shape: (n_samples, {pca.n_features_in_})")
print(f"   - Output shape: (n_samples, {pca.n_components_})")

# Load model
print("\nLoading XGBoost model...")
with open(f"{model_path}\\xgboost_model.pkl", 'rb') as f:
    model = pickle.load(f)
print(f"✅ Model loaded")
print(f"   - n_features: {model.n_features_in_}")
print(f"   - Expected input shape: (n_samples, {model.n_features_in_})")

print("\n" + "=" * 80)
print("FEATURE DIMENSION ANALYSIS")
print("=" * 80)
print(f"\nDatabase has 6 feature columns: LAT, LON, SOG, COG, Heading, VesselType")
print(f"  - 6 dimensions × 17 features per dimension = 96 features")
print(f"  - Plus 7 Haversine features = 103 total features")
print(f"\nScaler expects: {scaler.n_features_in_} features")
print(f"PCA expects: {pca.n_features_in_} features")
print(f"Model expects: {model.n_features_in_} features")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if scaler.n_features_in_ == 103:
    print("✅ Scaler matches database features (103)")
else:
    print(f"❌ Scaler mismatch: expects {scaler.n_features_in_}, database has 103")

if pca.n_features_in_ == scaler.n_features_in_:
    print(f"✅ PCA input matches scaler output ({pca.n_features_in_})")
else:
    print(f"❌ PCA input mismatch: expects {pca.n_features_in_}, scaler outputs {scaler.n_features_in_}")

if model.n_features_in_ == pca.n_components_:
    print(f"✅ Model input matches PCA output ({model.n_features_in_})")
else:
    print(f"❌ Model input mismatch: expects {model.n_features_in_}, PCA outputs {pca.n_components_}")

