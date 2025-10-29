"""
Analyze the preprocessed cached data for documentation
"""
import numpy as np
import json

cache_file = r'F:\PyTorch_GPU\maritime_vessel_forecasting\Multi_vessel_forecasting\results\cache\seq_cache_len12_sampled_3pct.npz'

try:
    data = np.load(cache_file)
    X = data['X']
    y = data['y']
    
    print("=" * 80)
    print("PREPROCESSED DATA ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 DATA DIMENSIONS:")
    print(f"  X shape: {X.shape} (samples, timesteps, features)")
    print(f"  y shape: {y.shape} (samples, outputs)")
    print(f"  Number of samples: {X.shape[0]}")
    print(f"  Sequence length (timesteps): {X.shape[1]}")
    print(f"  Input features per timestep: {X.shape[2]}")
    print(f"  Output dimensions: {y.shape[1]}")
    
    print(f"\n📈 DATA STATISTICS:")
    print(f"  X - Min: {X.min():.6f}, Max: {X.max():.6f}, Mean: {X.mean():.6f}, Std: {X.std():.6f}")
    print(f"  y - Min: {y.min():.6f}, Max: {y.max():.6f}, Mean: {y.mean():.6f}, Std: {y.std():.6f}")
    
    print(f"\n🔍 FEATURE ANALYSIS:")
    print(f"  Total features per sample: {X.shape[2] * X.shape[1]}")
    print(f"  Features per timestep: {X.shape[2]}")
    print(f"  Expected features after extraction: 483 (28 dims × 17 features + 7 Haversine)")
    
    print(f"\n📋 CACHE FILE INFO:")
    print(f"  Keys in cache: {list(data.keys())}")
    print(f"  Cache file size: {np.prod(X.shape) * 8 / (1024**2):.2f} MB (X)")
    print(f"  Cache file size: {np.prod(y.shape) * 8 / (1024**2):.2f} MB (y)")
    
    print(f"\n✅ Data loaded successfully!")
    
    # Save analysis to JSON
    analysis = {
        "X_shape": list(X.shape),
        "y_shape": list(y.shape),
        "X_stats": {
            "min": float(X.min()),
            "max": float(X.max()),
            "mean": float(X.mean()),
            "std": float(X.std())
        },
        "y_stats": {
            "min": float(y.min()),
            "max": float(y.max()),
            "mean": float(y.mean()),
            "std": float(y.std())
        },
        "cache_keys": list(data.keys())
    }
    
    with open('data_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n✅ Analysis saved to data_analysis.json")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

