"""
Test XGBoost Integration with Maritime Defense Dashboard
Tests the prediction endpoints and model loading
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.xgboost_predictor import get_predictor
from app.db_handler import MaritimeDB

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_model_loading():
    """Test XGBoost model loading"""
    print_section("🤖 MODEL LOADING TEST")
    
    try:
        predictor = get_predictor()
        
        if predictor.is_loaded:
            print("✅ Model loaded successfully")
            print(f"   - XGBoost model: {predictor.model is not None}")
            print(f"   - StandardScaler: {predictor.scaler is not None}")
            print(f"   - PCA transformer: {predictor.pca is not None}")
            return True
        else:
            print("⚠️  Model not loaded (files may not exist)")
            print("   This is expected if model files are not in results/xgboost_advanced_50_vessels/")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print_section("🗄️  DATABASE CONNECTION TEST")
    
    try:
        base_dir = os.path.dirname(__file__)
        db_path = os.path.join(base_dir, "maritime_data.db")
        
        if not os.path.exists(db_path):
            db_path = os.path.join(base_dir, "maritime_sample_0104.db")
        
        if not os.path.exists(db_path):
            print(f"❌ No database found at {db_path}")
            return False
        
        db = MaritimeDB(db_path)
        vessels = db.get_all_vessel_names()
        
        print(f"✅ Database connected")
        print(f"   - Database: {db_path}")
        print(f"   - Vessels available: {len(vessels)}")
        
        if vessels:
            print(f"   - Sample vessels: {vessels[:3]}")
        
        return True, db, vessels
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False, None, []

def test_api_endpoints():
    """Test FastAPI endpoints"""
    print_section("🌐 API ENDPOINTS TEST")
    
    backend_url = "http://127.0.0.1:8000"
    
    # Test 1: Check if backend is running
    print("Test 1: Backend Health Check")
    try:
        response = requests.get(f"{backend_url}/vessels", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            vessels = response.json().get("vessels", [])
            print(f"   - Available vessels: {len(vessels)}")
            return True, vessels
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False, []
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://127.0.0.1:8000")
        print("   Make sure backend is running: uvicorn app.main:app --reload")
        return False, []
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, []

def test_prediction_endpoint(vessel_name):
    """Test prediction endpoint"""
    print_section(f"🎯 PREDICTION TEST - {vessel_name}")
    
    backend_url = "http://127.0.0.1:8000"
    
    try:
        print(f"Requesting prediction for: {vessel_name}")
        response = requests.post(
            f"{backend_url}/predict/trajectory",
            json={
                "vessel": vessel_name,
                "sequence_length": 12
            },
            timeout=30
        )
        
        result = response.json()
        
        if result.get("prediction_available"):
            print("✅ Prediction successful")
            print(f"   - Vessel: {result['vessel_name']}")
            print(f"   - MMSI: {result['mmsi']}")
            print(f"   - Current Position: ({result['last_known_lat']:.4f}, {result['last_known_lon']:.4f})")
            print(f"   - Predicted Position: ({result['predicted_lat']:.4f}, {result['predicted_lon']:.4f})")
            print(f"   - Current SOG: {result['last_known_sog']:.2f} knots")
            print(f"   - Predicted SOG: {result['predicted_sog']:.2f} knots")
            print(f"   - Current COG: {result['last_known_cog']:.0f}°")
            print(f"   - Predicted COG: {result['predicted_cog']:.0f}°")
            
            if "map_data" in result:
                print(f"   - Map data included: Yes")
            
            return True
        else:
            print(f"⚠️  Prediction not available: {result.get('error', 'Unknown error')}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Request timeout (30s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🧪 XGBOOST INTEGRATION TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: Model Loading
    results["model_loading"] = test_model_loading()
    
    # Test 2: Database Connection
    db_result = test_database_connection()
    results["database"] = db_result[0]
    db = db_result[1]
    vessels = db_result[2]
    
    # Test 3: API Endpoints
    api_result = test_api_endpoints()
    results["api_health"] = api_result[0]
    api_vessels = api_result[1]
    
    # Test 4: Prediction Endpoint (if backend is running and vessels available)
    if results["api_health"] and api_vessels:
        test_vessel = api_vessels[0]
        results["prediction"] = test_prediction_endpoint(test_vessel)
    else:
        print_section("⏭️  SKIPPING PREDICTION TEST")
        print("Backend not running or no vessels available")
        results["prediction"] = None
    
    # Summary
    print_section("📊 TEST SUMMARY")
    
    print("Results:")
    print(f"  ✅ Model Loading: {'PASS' if results['model_loading'] else 'FAIL/SKIP'}")
    print(f"  ✅ Database: {'PASS' if results['database'] else 'FAIL'}")
    print(f"  ✅ API Health: {'PASS' if results['api_health'] else 'FAIL'}")
    print(f"  ✅ Prediction: {'PASS' if results['prediction'] else 'FAIL/SKIP'}")
    
    print("\n" + "="*70)
    print("  ✅ INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")
    
    return 0 if all(v for v in results.values() if v is not None) else 1

if __name__ == "__main__":
    sys.exit(main())

