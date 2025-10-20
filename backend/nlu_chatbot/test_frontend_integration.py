#!/usr/bin/env python
"""
Test script to verify frontend integration with backend
Tests: API responses, formatted responses, map data
"""
import sys
import os
sys.path.insert(0, 'src')

import requests
import json
from datetime import datetime

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_backend_running():
    """Test if backend is running"""
    print_section("TEST 1: Backend Connection")
    
    try:
        r = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if r.status_code == 200:
            print("✅ Backend is running on http://127.0.0.1:8000")
            return True
        else:
            print(f"❌ Backend returned status {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure backend is running: uvicorn main:app --reload")
        return False

def test_query_endpoint():
    """Test query endpoint"""
    print_section("TEST 2: Query Endpoint")
    
    test_queries = [
        "show LAVACA",
        "show TREASURE COAST",
        "where is LAVACA",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        try:
            r = requests.post(
                "http://127.0.0.1:8000/query",
                json={"text": query},
                timeout=10
            )
            
            if r.status_code == 200:
                payload = r.json()
                parsed = payload.get("parsed", {})
                response = payload.get("response", {})
                formatted = payload.get("formatted_response", "")
                
                print(f"   ✅ Status: 200 OK")
                print(f"   Intent: {parsed.get('intent')}")
                print(f"   Vessel: {parsed.get('vessel_name')}")
                
                if formatted:
                    print(f"   Formatted: {formatted[:80]}...")
                
                if 'VesselName' in response:
                    print(f"   Position: {response.get('LAT')}, {response.get('LON')}")
                    print(f"   Speed: {response.get('SOG')} knots")
                    
                    if 'track' in response:
                        print(f"   Track points: {len(response['track'])}")
            else:
                print(f"   ❌ Status: {r.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_formatted_response():
    """Test formatted response field"""
    print_section("TEST 3: Formatted Response Field")
    
    try:
        r = requests.post(
            "http://127.0.0.1:8000/query",
            json={"text": "show LAVACA"},
            timeout=10
        )
        
        payload = r.json()
        formatted = payload.get("formatted_response", "")
        
        if formatted:
            print("✅ Formatted response field present")
            print(f"\nFormatted Response:")
            print(f"  {formatted}")
            
            # Check for key elements
            checks = [
                ("Vessel name", "LAVACA" in formatted or "Lavaca" in formatted),
                ("Position info", "°" in formatted or "position" in formatted.lower()),
                ("Speed info", "knots" in formatted.lower() or "speed" in formatted.lower()),
            ]
            
            print("\nContent checks:")
            for check_name, result in checks:
                status = "✅" if result else "⚠️"
                print(f"  {status} {check_name}")
        else:
            print("❌ No formatted response field")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_track_data():
    """Test track data in response"""
    print_section("TEST 4: Track Data")
    
    try:
        r = requests.post(
            "http://127.0.0.1:8000/query",
            json={"text": "show LAVACA"},
            timeout=10
        )
        
        payload = r.json()
        response = payload.get("response", {})
        
        if 'track' in response and isinstance(response['track'], list):
            track = response['track']
            print(f"✅ Track data present: {len(track)} points")
            
            if len(track) > 0:
                first_point = track[0]
                print(f"\nFirst point:")
                print(f"  LAT: {first_point.get('LAT')}")
                print(f"  LON: {first_point.get('LON')}")
                print(f"  Time: {first_point.get('BaseDateTime')}")
                print(f"  Speed: {first_point.get('SOG')}")
                print(f"  Course: {first_point.get('COG')}")
                
                # Check for required fields
                required_fields = ['LAT', 'LON', 'BaseDateTime']
                all_present = all(field in first_point for field in required_fields)
                
                if all_present:
                    print("\n✅ All required fields present for mapping")
                else:
                    print("\n⚠️ Some fields missing for mapping")
        else:
            print("⚠️ No track data in response")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_vessel_search():
    """Test vessel search endpoint"""
    print_section("TEST 5: Vessel Search")
    
    try:
        r = requests.get(
            "http://127.0.0.1:8000/vessels/search",
            params={"q": "LAV", "limit": 10},
            timeout=10
        )
        
        if r.status_code == 200:
            payload = r.json()
            vessels = payload.get("vessels", [])
            
            print(f"✅ Search returned {len(vessels)} vessels")
            if vessels:
                print(f"   Sample: {vessels[:3]}")
        else:
            print(f"❌ Status: {r.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def test_response_structure():
    """Test response structure for frontend"""
    print_section("TEST 6: Response Structure")
    
    try:
        r = requests.post(
            "http://127.0.0.1:8000/query",
            json={"text": "show LAVACA"},
            timeout=10
        )
        
        payload = r.json()
        
        # Check required fields
        required_fields = ['parsed', 'response', 'formatted_response']
        
        print("Response structure check:")
        for field in required_fields:
            if field in payload:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} (MISSING)")
        
        # Check parsed structure
        parsed = payload.get('parsed', {})
        parsed_fields = ['intent', 'vessel_name', 'datetime']
        
        print("\nParsed structure check:")
        for field in parsed_fields:
            if field in parsed:
                print(f"  ✅ {field}: {parsed[field]}")
            else:
                print(f"  ⚠️ {field} (optional)")
        
        # Check response structure
        response = payload.get('response', {})
        response_fields = ['VesselName', 'LAT', 'LON', 'SOG', 'COG', 'BaseDateTime']
        
        print("\nResponse structure check:")
        for field in response_fields:
            if field in response:
                print(f"  ✅ {field}")
            else:
                print(f"  ⚠️ {field} (optional)")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MARITIME NLU - FRONTEND INTEGRATION TEST")
    print("="*70)
    
    # Test 1: Backend connection
    if not test_backend_running():
        print("\n❌ Backend not running. Please start it first:")
        print("   cd backend/nlu_chatbot/src/app")
        print("   uvicorn main:app --reload")
        return False
    
    # Test 2: Query endpoint
    test_query_endpoint()
    
    # Test 3: Formatted response
    test_formatted_response()
    
    # Test 4: Track data
    test_track_data()
    
    # Test 5: Vessel search
    test_vessel_search()
    
    # Test 6: Response structure
    test_response_structure()
    
    print_section("ALL TESTS COMPLETE")
    print("\n✅ Frontend integration test suite finished!")
    print("\nNext steps:")
    print("  1. Start frontend: cd backend/nlu_chatbot/frontend && streamlit run app.py")
    print("  2. Open http://localhost:8501")
    print("  3. Try queries like 'show LAVACA'")
    print("  4. Check formatted responses and maps")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

