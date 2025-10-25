"""
Comprehensive test of real XGBoost predictions
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import sqlite3
import time
import random
from collections import defaultdict

# Get 25 random vessels
conn = sqlite3.connect('backend/nlu_chatbot/maritime_sample_0104.db')
cursor = conn.cursor()
cursor.execute("""
SELECT DISTINCT VesselName FROM vessel_data 
WHERE VesselName IS NOT NULL 
ORDER BY RANDOM() LIMIT 25
""")
vessels = [row[0] for row in cursor.fetchall()]
conn.close()

print(f"\n{'='*80}")
print("COMPREHENSIVE XGBOOST PREDICTION TEST")
print(f"{'='*80}")
print(f"Testing {len(vessels)} vessels with 4 sequence lengths each")
print(f"Total tests: {len(vessels) * 4}")

backend_url = "http://127.0.0.1:8000"

# Test predictions
results = {
    "total_tests": 0,
    "successful": 0,
    "failed": 0,
    "real_mode": 0,
    "demo_mode": 0,
    "by_seq_len": defaultdict(lambda: {"total": 0, "real": 0, "demo": 0, "failed": 0}),
    "errors": defaultdict(int)
}

print(f"\nRunning tests...")
for i, vessel_name in enumerate(vessels, 1):
    print(f"\n[{i}/{len(vessels)}] {vessel_name}")
    
    for seq_len in [6, 12, 18, 24]:
        results["total_tests"] += 1
        results["by_seq_len"][seq_len]["total"] += 1
        
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
                        results["by_seq_len"][seq_len]["real"] += 1
                        print(f"  ✅ REAL (seq={seq_len}): LAT={data['predicted_lat']:.4f}, LON={data['predicted_lon']:.4f}")
                    else:
                        results["demo_mode"] += 1
                        results["by_seq_len"][seq_len]["demo"] += 1
                        print(f"  ⚠️  DEMO (seq={seq_len})")
                else:
                    results["failed"] += 1
                    results["by_seq_len"][seq_len]["failed"] += 1
                    error = data.get("error", "Unknown error")
                    results["errors"][error] += 1
                    print(f"  ❌ Failed (seq={seq_len}): {error}")
            else:
                results["failed"] += 1
                results["by_seq_len"][seq_len]["failed"] += 1
                print(f"  ❌ HTTP {response.status_code} (seq={seq_len})")
                
        except Exception as e:
            results["failed"] += 1
            results["by_seq_len"][seq_len]["failed"] += 1
            error_msg = str(e)
            results["errors"][error_msg] += 1
            print(f"  ❌ Exception (seq={seq_len}): {error_msg}")

print(f"\n{'='*80}")
print("FINAL RESULTS")
print(f"{'='*80}")
print(f"Total tests: {results['total_tests']}")
print(f"Successful: {results['successful']} ({100*results['successful']/results['total_tests']:.1f}%)")
print(f"Failed: {results['failed']} ({100*results['failed']/results['total_tests']:.1f}%)")
print(f"\nModel Mode Distribution:")
print(f"  REAL mode: {results['real_mode']} ({100*results['real_mode']/results['successful']:.1f}% of successful)")
print(f"  DEMO mode: {results['demo_mode']} ({100*results['demo_mode']/results['successful']:.1f}% of successful)")

print(f"\nBy Sequence Length:")
for seq_len in sorted(results["by_seq_len"].keys()):
    stats = results["by_seq_len"][seq_len]
    success_rate = 100 * (stats["real"] + stats["demo"]) / stats["total"]
    print(f"  {seq_len} points: {stats['real']+stats['demo']}/{stats['total']} successful ({success_rate:.1f}%)")
    print(f"    - REAL: {stats['real']}, DEMO: {stats['demo']}, Failed: {stats['failed']}")

if results['errors']:
    print(f"\nErrors encountered:")
    for error, count in sorted(results['errors'].items(), key=lambda x: -x[1]):
        print(f"  - {error}: {count} times")

print(f"\n{'='*80}")
if results['real_mode'] > 0:
    print(f"✅ SUCCESS: {results['real_mode']} real predictions out of {results['successful']} successful!")
    print(f"   Real mode success rate: {100*results['real_mode']/results['successful']:.1f}%")
else:
    print("⚠️  WARNING: Still using DEMO mode")
print(f"{'='*80}\n")

# Save results
with open('xgboost_real_test_results.json', 'w') as f:
    json.dump({
        "total_tests": results["total_tests"],
        "successful": results["successful"],
        "failed": results["failed"],
        "real_mode": results["real_mode"],
        "demo_mode": results["demo_mode"],
        "success_rate": 100 * results["successful"] / results["total_tests"],
        "real_mode_rate": 100 * results["real_mode"] / results["successful"] if results["successful"] > 0 else 0,
        "by_sequence_length": {str(k): dict(v) for k, v in results["by_seq_len"].items()}
    }, f, indent=2)

print("Results saved to xgboost_real_test_results.json")

