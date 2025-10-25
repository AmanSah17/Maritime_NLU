"""
Analyze the training data to understand feature extraction
"""
import pickle
import numpy as np
import pandas as pd
import sqlite3

# Load training data to understand feature extraction
print("=" * 80)
print("ANALYZING TRAINING DATA FEATURES")
print("=" * 80)

# Get a sample vessel from database
conn = sqlite3.connect('backend/nlu_chatbot/maritime_sample_0104.db')
query = """
SELECT MMSI, BaseDateTime, LAT, LON, SOG, COG, Heading, VesselName, CallSign, VesselType
FROM vessel_data
WHERE VesselName IS NOT NULL
LIMIT 1
"""
df = pd.read_sql_query(query, conn)
conn.close()

print(f"\nSample vessel data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Now let's manually extract features like the training code does
print("\n" + "=" * 80)
print("MANUAL FEATURE EXTRACTION (4 dimensions)")
print("=" * 80)

features = []
feature_names = []

# Extract features for each dimension (LAT, LON, SOG, COG)
for col in ['LAT', 'LON', 'SOG', 'COG']:
    if col in df.columns:
        values = df[col].values.astype(float)
        print(f"\n{col}: {len(values)} values")
        
        # Statistical features (10)
        stat_features = [
            np.mean(values),
            np.std(values),
            np.min(values),
            np.max(values),
            np.median(values),
            np.percentile(values, 25),
            np.percentile(values, 75),
            np.max(values) - np.min(values),
            pd.Series(values).skew(),
            pd.Series(values).kurtosis()
        ]
        features.extend(stat_features)
        feature_names.extend([f"{col}_mean", f"{col}_std", f"{col}_min", f"{col}_max", 
                             f"{col}_median", f"{col}_p25", f"{col}_p75", f"{col}_range",
                             f"{col}_skew", f"{col}_kurtosis"])
        
        print(f"  Statistical features (10): {len(stat_features)}")
        
        # Trend features (7)
        if len(values) > 1:
            diff = np.diff(values)
            trend = np.polyfit(range(len(values)), values, 1)[0]
            trend_features = [
                trend,
                np.std(diff),
                np.max(diff),
                np.min(diff),
                values[-1] - values[0],
                values[-1] / (values[0] + 1e-6),
                np.std(diff) / (np.mean(values) + 1e-6)
            ]
            features.extend(trend_features)
            feature_names.extend([f"{col}_trend", f"{col}_trend_std", f"{col}_trend_max", 
                                 f"{col}_trend_min", f"{col}_first_last_diff", 
                                 f"{col}_first_last_ratio", f"{col}_volatility"])
            print(f"  Trend features (7): {len(trend_features)}")

print(f"\nTotal features from 4 dimensions: {len(features)}")
print(f"  - 4 dimensions × 10 statistical = 40")
print(f"  - 4 dimensions × 7 trend = 28")
print(f"  - Subtotal: 68")

# Haversine distance features (7)
if 'LAT' in df.columns and 'LON' in df.columns:
    lats = df['LAT'].values
    lons = df['LON'].values
    
    # Distance to first point
    dist_to_first = []
    for i in range(len(lats)):
        R = 6371
        lat1_rad = np.radians(lats[0])
        lat2_rad = np.radians(lats[i])
        delta_lat = np.radians(lats[i] - lats[0])
        delta_lon = np.radians(lons[i] - lons[0])
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        dist = R * c
        dist_to_first.append(dist)
    
    # Consecutive distances
    consecutive_dists = [0.0]
    for i in range(1, len(lats)):
        R = 6371
        lat1_rad = np.radians(lats[i-1])
        lat2_rad = np.radians(lats[i])
        delta_lat = np.radians(lats[i] - lats[i-1])
        delta_lon = np.radians(lons[i] - lons[i-1])
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        dist = R * c
        consecutive_dists.append(dist)
    
    haversine_features = [
        np.mean(dist_to_first),
        np.max(dist_to_first),
        np.std(dist_to_first),
        np.sum(consecutive_dists),
        np.mean(consecutive_dists[1:]) if len(consecutive_dists) > 1 else 0,
        np.max(consecutive_dists),
        np.std(consecutive_dists)
    ]
    features.extend(haversine_features)
    feature_names.extend(["haversine_mean_to_first", "haversine_max_to_first", 
                         "haversine_std_to_first", "haversine_sum_consecutive",
                         "haversine_mean_consecutive", "haversine_max_consecutive",
                         "haversine_std_consecutive"])
    print(f"\nHaversine features (7): {len(haversine_features)}")

print(f"\nTotal features extracted: {len(features)}")
print(f"Expected by model: 483")
print(f"\nDifference: {483 - len(features)} features")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print(f"The training data likely had MORE dimensions than just LAT, LON, SOG, COG")
print(f"Possible additional dimensions:")
print(f"  - Heading (already in database)")
print(f"  - VesselType (already in database)")
print(f"  - Derived features (speed components, acceleration, etc.)")
print(f"  - Or the model was trained on 28 raw dimensions total")
print(f"\nTo use the model, we need to match the 483-feature input exactly.")

