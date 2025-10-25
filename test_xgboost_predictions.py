"""
Comprehensive XGBoost Prediction Testing Script
Tests 25 random vessels with different timestamps and prediction horizons
"""

import requests
import json
import random
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
DB_PATH = "backend/nlu_chatbot/maritime_sample_0104.db"
NUM_VESSELS = 25
SEQUENCE_LENGTHS = [6, 12, 18, 24]

# Setup plotting
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (16, 12)

class XGBoostTester:
    def __init__(self, backend_url, db_path):
        self.backend_url = backend_url
        self.db_path = db_path
        self.results = []
        self.errors = []
        
    def get_random_vessels(self, n=25):
        """Get n random vessels from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT DISTINCT VesselName FROM vessel_data ORDER BY RANDOM() LIMIT ?"
            vessels = pd.read_sql_query(query, conn, params=(n,))
            conn.close()
            return vessels['VesselName'].tolist()
        except Exception as e:
            print(f"❌ Error fetching vessels: {e}")
            return []
    
    def get_vessel_data_count(self, vessel_name):
        """Get number of data points for a vessel"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT COUNT(*) as count FROM vessel_data WHERE VesselName = ?"
            result = pd.read_sql_query(query, conn, params=(vessel_name,))
            conn.close()
            return result['count'].iloc[0]
        except Exception as e:
            print(f"❌ Error getting data count: {e}")
            return 0
    
    def test_prediction(self, vessel_name, sequence_length=12):
        """Test prediction for a vessel"""
        try:
            payload = {
                "vessel": vessel_name,
                "sequence_length": sequence_length
            }
            
            response = requests.post(
                f"{self.backend_url}/predict/trajectory",
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            # Check if prediction was successful
            if result.get("prediction_available"):
                return {
                    "vessel": vessel_name,
                    "sequence_length": sequence_length,
                    "status": "✅ SUCCESS",
                    "model_mode": result.get("model_mode", "UNKNOWN"),
                    "predicted_lat": result.get("predicted_lat"),
                    "predicted_lon": result.get("predicted_lon"),
                    "predicted_sog": result.get("predicted_sog"),
                    "predicted_cog": result.get("predicted_cog"),
                    "last_known_lat": result.get("last_known_lat"),
                    "last_known_lon": result.get("last_known_lon"),
                    "last_known_sog": result.get("last_known_sog"),
                    "last_known_cog": result.get("last_known_cog"),
                    "error": None
                }
            else:
                error_msg = result.get("error", "Unknown error")
                return {
                    "vessel": vessel_name,
                    "sequence_length": sequence_length,
                    "status": "❌ FAILED",
                    "model_mode": "N/A",
                    "error": error_msg
                }
        except Exception as e:
            return {
                "vessel": vessel_name,
                "sequence_length": sequence_length,
                "status": "❌ ERROR",
                "model_mode": "N/A",
                "error": str(e)
            }
    
    def run_tests(self):
        """Run comprehensive tests"""
        print("\n" + "="*80)
        print("🚢 XGBoost Prediction Testing Suite")
        print("="*80)
        
        # Get random vessels
        print(f"\n📊 Fetching {NUM_VESSELS} random vessels...")
        vessels = self.get_random_vessels(NUM_VESSELS)
        
        if not vessels:
            print("❌ No vessels found!")
            return
        
        print(f"✅ Found {len(vessels)} vessels")
        
        # Test each vessel with different sequence lengths
        total_tests = len(vessels) * len(SEQUENCE_LENGTHS)
        test_count = 0
        
        for vessel in vessels:
            data_count = self.get_vessel_data_count(vessel)
            print(f"\n🚢 Testing {vessel} ({data_count} data points)")
            
            for seq_len in SEQUENCE_LENGTHS:
                test_count += 1
                print(f"  [{test_count}/{total_tests}] Sequence length: {seq_len}...", end=" ")
                
                result = self.test_prediction(vessel, seq_len)
                self.results.append(result)
                
                if result["status"] == "✅ SUCCESS":
                    print(f"✅ {result['model_mode']}")
                else:
                    print(f"{result['status']}")
                    if result.get("error"):
                        print(f"       Error: {result['error']}")
        
        print("\n" + "="*80)
        print("📈 Test Summary")
        print("="*80)
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        df = pd.DataFrame(self.results)
        
        # Count by status
        status_counts = df['status'].value_counts()
        print("\n📊 Status Distribution:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Count by model mode
        successful = df[df['status'] == "✅ SUCCESS"]
        if len(successful) > 0:
            print("\n🤖 Model Mode Distribution (Successful):")
            mode_counts = successful['model_mode'].value_counts()
            for mode, count in mode_counts.items():
                print(f"  {mode}: {count}")
        
        # Sequence length analysis
        print("\n📏 Sequence Length Analysis:")
        for seq_len in SEQUENCE_LENGTHS:
            seq_results = df[df['sequence_length'] == seq_len]
            success_count = len(seq_results[seq_results['status'] == "✅ SUCCESS"])
            total = len(seq_results)
            print(f"  Length {seq_len}: {success_count}/{total} successful ({100*success_count/total:.1f}%)")
        
        # Error analysis
        errors = df[df['status'] != "✅ SUCCESS"]
        if len(errors) > 0:
            print("\n⚠️  Error Analysis:")
            error_types = errors['error'].value_counts()
            for error, count in error_types.head(5).items():
                print(f"  {error}: {count}")
    
    def plot_results(self):
        """Plot prediction results"""
        df = pd.DataFrame(self.results)
        successful = df[df['status'] == "✅ SUCCESS"]
        
        if len(successful) == 0:
            print("❌ No successful predictions to plot")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('XGBoost Prediction Results - 25 Random Vessels', fontsize=16, fontweight='bold')
        
        # 1. Status distribution
        ax = axes[0, 0]
        status_counts = df['status'].value_counts()
        colors = ['#00D9FF', '#FF6B6B', '#FFD93D']
        ax.bar(status_counts.index, status_counts.values, color=colors[:len(status_counts)])
        ax.set_title('Prediction Status Distribution', fontweight='bold')
        ax.set_ylabel('Count')
        for i, v in enumerate(status_counts.values):
            ax.text(i, v + 0.5, str(v), ha='center', fontweight='bold')
        
        # 2. Success rate by sequence length
        ax = axes[0, 1]
        seq_success = []
        for seq_len in SEQUENCE_LENGTHS:
            seq_results = df[df['sequence_length'] == seq_len]
            success_rate = len(seq_results[seq_results['status'] == "✅ SUCCESS"]) / len(seq_results) * 100
            seq_success.append(success_rate)
        
        ax.plot(SEQUENCE_LENGTHS, seq_success, marker='o', linewidth=2, markersize=10, color='#00D9FF')
        ax.set_title('Success Rate by Sequence Length', fontweight='bold')
        ax.set_xlabel('Sequence Length')
        ax.set_ylabel('Success Rate (%)')
        ax.set_ylim([0, 105])
        ax.grid(True, alpha=0.3)
        for i, v in enumerate(seq_success):
            ax.text(SEQUENCE_LENGTHS[i], v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # 3. Prediction scatter (LAT/LON)
        ax = axes[1, 0]
        if len(successful) > 0:
            ax.scatter(successful['last_known_lon'], successful['last_known_lat'], 
                      label='Current Position', s=100, alpha=0.6, color='#00CC44')
            ax.scatter(successful['predicted_lon'], successful['predicted_lat'], 
                      label='Predicted Position', s=100, alpha=0.6, color='#00D9FF')
            
            # Draw arrows from current to predicted
            for idx, row in successful.iterrows():
                ax.arrow(row['last_known_lon'], row['last_known_lat'],
                        row['predicted_lon'] - row['last_known_lon'],
                        row['predicted_lat'] - row['last_known_lat'],
                        head_width=0.01, head_length=0.01, fc='#FF9900', ec='#FF9900', alpha=0.3)
        
        ax.set_title('Vessel Positions: Current vs Predicted', fontweight='bold')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. Speed and Course predictions
        ax = axes[1, 1]
        if len(successful) > 0:
            x = np.arange(len(successful))
            width = 0.35
            
            ax.bar(x - width/2, successful['last_known_sog'], width, label='Current SOG', alpha=0.8, color='#00CC44')
            ax.bar(x + width/2, successful['predicted_sog'], width, label='Predicted SOG', alpha=0.8, color='#00D9FF')
            
            ax.set_title('Speed of Ground (SOG) Comparison', fontweight='bold')
            ax.set_ylabel('SOG (knots)')
            ax.set_xlabel('Vessel Index')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('xgboost_prediction_results.png', dpi=150, bbox_inches='tight')
        print("\n✅ Plot saved as 'xgboost_prediction_results.png'")
        plt.show()
    
    def save_results(self, filename='xgboost_test_results.json'):
        """Save results to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n✅ Results saved to '{filename}'")


if __name__ == "__main__":
    tester = XGBoostTester(BACKEND_URL, DB_PATH)
    
    # Run tests
    results = tester.run_tests()
    
    # Save results
    tester.save_results()
    
    # Plot results
    tester.plot_results()
    
    print("\n" + "="*80)
    print("✅ Testing Complete!")
    print("="*80)

