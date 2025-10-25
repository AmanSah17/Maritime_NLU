"""
Test real XGBoost predictions with the fixed adapter
"""
import requests
import json
import sqlite3
import time
import random

# Wait for backend to start
print("Waiting for backend to start...")
time.sleep(3)

# Get a sample vessel
conn = sqlite3.connect('backend/nlu_chatbot/maritime_sample_0104.db')
cursor = conn.cursor()
cursor.execute("""
SELECT DISTINCT VesselName FROM vessel_data 
WHERE VesselName IS NOT NULL 
ORDER BY RANDOM() LIMIT 5
""")
vessels = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"\n{'='*80}")
print("TESTING REAL XGBOOST PREDICTIONS")
print(f"{'='*80}")

backend_url = "http://127.0.0.1:8000"

# Test health
print("\n1. Testing backend health...")
try:
    response = requests.get(f"{backend_url}/health", timeout=5)
    print(f"✅ Backend is running: {response.status_code}")
except Exception as e:
    print(f"❌ Backend error: {e}")
    exit(1)

# Test predictions
print(f"\n2. Testing predictions on {len(vessels)} vessels...")
results = {
    "total_tests": 0,
    "successful": 0,
    "failed": 0,
    "real_mode": 0,
    "demo_mode": 0,
    "errors": []
}

for vessel_name in vessels:
    for seq_len in [6, 12, 18]:
        results["total_tests"] += 1
        
        try:
            response = requests.post(
                f"{backend_url}/predict/trajectory",
                json={"vessel": vessel_name, "sequence_length": seq_len},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("prediction_available"):
                    results["successful"] += 1
                    model_mode = data.get("model_mode", "UNKNOWN")
                    
                    if model_mode == "REAL":
                        results["real_mode"] += 1
                        print(f"✅ REAL: {vessel_name} (seq_len={seq_len})")
                        print(f"   Predicted: LAT={data['predicted_lat']:.4f}, LON={data['predicted_lon']:.4f}")
                    else:
                        results["demo_mode"] += 1
                        print(f"⚠️  DEMO: {vessel_name} (seq_len={seq_len})")
                else:
                    results["failed"] += 1
                    error = data.get("error", "Unknown error")
                    print(f"❌ Failed: {vessel_name} - {error}")
                    results["errors"].append(error)
            else:
                results["failed"] += 1
                print(f"❌ HTTP {response.status_code}: {vessel_name}")
                
        except Exception as e:
            results["failed"] += 1
            print(f"❌ Exception: {vessel_name} - {str(e)}")
            results["errors"].append(str(e))

print(f"\n{'='*80}")
print("TEST RESULTS")
print(f"{'='*80}")
print(f"Total tests: {results['total_tests']}")
print(f"Successful: {results['successful']} ({100*results['successful']/results['total_tests']:.1f}%)")
print(f"Failed: {results['failed']}")
print(f"REAL mode: {results['real_mode']}")
print(f"DEMO mode: {results['demo_mode']}")

if results['errors']:
    print(f"\nErrors encountered:")
    for error in set(results['errors']):
        print(f"  - {error}")

print(f"\n{'='*80}")
if results['real_mode'] > 0:
    print("✅ SUCCESS: Real XGBoost predictions are working!")
else:
    print("⚠️  WARNING: Still using DEMO mode")
print(f"{'='*80}")

