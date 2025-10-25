import numpy as np

# Check the cache file to see the actual dimensions
cache_file = 'F:\\PyTorch_GPU\\maritime_vessel_forecasting\\Multi_vessel_forecasting\\results\\cache\\seq_cache_len12_sampled_3pct.npz'
try:
    data = np.load(cache_file)
    X = data['X']
    y = data['y']
    print(f"Training data shape: X={X.shape}, y={y.shape}")
    print(f"Number of samples: {X.shape[0]}")
    print(f"Number of timesteps: {X.shape[1]}")
    print(f"Number of features per timestep: {X.shape[2]}")
    print(f"\nFeature extraction calculation:")
    print(f"  {X.shape[2]} dimensions × 17 features per dimension = {X.shape[2] * 17}")
    print(f"  Plus 7 Haversine features = {X.shape[2] * 17 + 7}")
    print(f"\nExpected by scaler: 483")
    print(f"Match: {X.shape[2] * 17 + 7 == 483}")
    
    if X.shape[2] * 17 + 7 == 483:
        print(f"\n✅ Confirmed: Model was trained on {X.shape[2]} dimensions")
        print(f"   {X.shape[2]} × 17 + 7 = 483 features")
except FileNotFoundError:
    print(f"Cache file not found: {cache_file}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

