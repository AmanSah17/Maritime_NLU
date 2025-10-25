import numpy as np
import pandas as pd

# Load training data
cache_file = 'F:\\PyTorch_GPU\\maritime_vessel_forecasting\\Multi_vessel_forecasting\\results\\cache\\seq_cache_len12_sampled_3pct.npz'
data = np.load(cache_file)
X = data['X']
y = data['y']

print("=" * 80)
print("TRAINING DATA ANALYSIS")
print("=" * 80)
print(f"\nX shape: {X.shape} (samples, timesteps, features)")
print(f"y shape: {y.shape} (samples, outputs)")
print(f"\nNumber of dimensions in training data: {X.shape[2]}")
print(f"Number of timesteps: {X.shape[1]}")
print(f"Number of output variables: {y.shape[1]}")

# Analyze the data
print("\n" + "=" * 80)
print("FEATURE STATISTICS")
print("=" * 80)

# Get statistics for each dimension
for dim in range(X.shape[2]):
    data_dim = X[:, :, dim].flatten()
    print(f"\nDimension {dim}:")
    print(f"  Min: {np.min(data_dim):.6f}")
    print(f"  Max: {np.max(data_dim):.6f}")
    print(f"  Mean: {np.mean(data_dim):.6f}")
    print(f"  Std: {np.std(data_dim):.6f}")
    
    # Try to identify what this dimension might be
    if np.min(data_dim) >= -90 and np.max(data_dim) <= 90:
        print(f"  → Likely: LATITUDE")
    elif np.min(data_dim) >= -180 and np.max(data_dim) <= 180:
        print(f"  → Likely: LONGITUDE")
    elif np.min(data_dim) >= 0 and np.max(data_dim) <= 360:
        print(f"  → Likely: HEADING or COG")
    elif np.min(data_dim) >= 0 and np.max(data_dim) <= 50:
        print(f"  → Likely: SOG (Speed Over Ground)")
    elif np.min(data_dim) >= 0 and np.max(data_dim) <= 100:
        print(f"  → Likely: VesselType or other categorical")
    else:
        print(f"  → Unknown")

print("\n" + "=" * 80)
print("OUTPUT VARIABLES")
print("=" * 80)
print(f"\nOutput shape: {y.shape}")
print(f"Number of output variables: {y.shape[1]}")
print("\nOutput statistics:")
for i in range(y.shape[1]):
    print(f"\nOutput {i}:")
    print(f"  Min: {np.min(y[:, i]):.6f}")
    print(f"  Max: {np.max(y[:, i]):.6f}")
    print(f"  Mean: {np.mean(y[:, i]):.6f}")
    print(f"  Std: {np.std(y[:, i]):.6f}")
    
    if i == 0:
        print(f"  → Likely: LATITUDE")
    elif i == 1:
        print(f"  → Likely: LONGITUDE")
    elif i == 2:
        print(f"  → Likely: SOG")
    elif i == 3:
        print(f"  → Likely: COG")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print(f"\nThe model was trained on {X.shape[2]} dimensions per timestep")
print(f"Database has only 6 dimensions: LAT, LON, SOG, COG, Heading, VesselType")
print(f"\nTo use the model, we need to either:")
print(f"1. Find the original training data with all 28 dimensions")
print(f"2. Retrain the model with the 6 available dimensions")
print(f"3. Use a different model or approach")

