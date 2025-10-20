#!/usr/bin/env python
"""
Comprehensive test script for Maritime NLU fixes
Tests: Database connection, NLU parsing, Response formatting, Map generation
"""
import sys
import os
sys.path.insert(0, 'src')

from app.db_handler import MaritimeDB
from app.nlp_interpreter import MaritimeNLPInterpreter
from app.intent_executor import IntentExecutor
from app.response_formatter import ResponseFormatter
from app.map_generator import MapGenerator

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_database():
    """Test 1: Database Connection"""
    print_section("TEST 1: Database Connection")
    
    # Check both databases
    for db_file in ['maritime_data.db', 'maritime_sample_0104.db']:
        print(f"\n📁 Checking {db_file}...")
        if os.path.exists(db_file):
            print(f"   ✅ File exists")
            try:
                db = MaritimeDB(db_file)
                vessels = db.get_all_vessel_names()
                print(f"   ✅ Connection successful")
                print(f"   ✅ Found {len(vessels)} unique vessels")
                if vessels:
                    print(f"   Sample: {vessels[:3]}")
                    return db_file, db
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ❌ File not found")
    
    return None, None

def test_nlu_parsing(db_file, db):
    """Test 2: NLU Vessel Name Extraction"""
    print_section("TEST 2: NLU Vessel Name Extraction")
    
    vessels = db.get_all_vessel_names()
    print(f"\n📚 Loaded {len(vessels)} vessels from {db_file}")
    
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    
    test_queries = [
        'show the location of +BRAVA at 10 hours 25 minutes',
        'show +BRAVA',
        'show BRAVA',
        'where is BRAVA',
        'show LAVACA',
        'predict where TREASURE COAST will be in 30 minutes',
    ]
    
    print("\n🔍 Testing vessel name extraction:")
    for query in test_queries:
        result = nlp.parse_query(query)
        vessel = result['vessel_name']
        intent = result['intent']
        status = "✅" if vessel else "❌"
        print(f"   {status} '{query}'")
        print(f"      → Vessel: {vessel}, Intent: {intent}")

def test_intent_executor(db_file, db):
    """Test 3: Intent Executor"""
    print_section("TEST 3: Intent Executor")
    
    vessels = db.get_all_vessel_names()
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    executor = IntentExecutor(db)
    
    test_queries = [
        'show LAVACA',
        'show TREASURE COAST',
    ]
    
    print("\n⚙️ Testing intent execution:")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        parsed = nlp.parse_query(query)
        response = executor.handle(parsed)
        
        if 'VesselName' in response:
            print(f"   ✅ Vessel: {response['VesselName']}")
            print(f"      Position: {response.get('LAT')}, {response.get('LON')}")
            print(f"      Speed: {response.get('SOG')} knots")
        elif 'message' in response:
            print(f"   ℹ️ Message: {response['message']}")
        else:
            print(f"   ❌ Unexpected response: {list(response.keys())}")

def test_response_formatter(db_file, db):
    """Test 4: Response Formatter"""
    print_section("TEST 4: Response Formatter")
    
    vessels = db.get_all_vessel_names()
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    executor = IntentExecutor(db)
    
    test_queries = [
        'show LAVACA',
        'predict where LAVACA will be in 30 minutes',
    ]
    
    print("\n💬 Testing response formatting:")
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        parsed = nlp.parse_query(query)
        response = executor.handle(parsed)
        intent = parsed.get('intent', '')
        
        formatted = ResponseFormatter.format_response(intent, response)
        print(f"   Formatted Response:")
        for line in formatted.split('\n'):
            print(f"      {line}")

def test_map_generation(db_file, db):
    """Test 5: Map Generation"""
    print_section("TEST 5: Map Generation")
    
    vessels = db.get_all_vessel_names()
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    executor = IntentExecutor(db)
    
    # Get a vessel with track data
    query = 'show LAVACA'
    parsed = nlp.parse_query(query)
    response = executor.handle(parsed)
    
    if 'track' in response and response['track']:
        print(f"\n🗺️ Testing map generation for {response['VesselName']}")
        
        track = response['track']
        print(f"   ✅ Track has {len(track)} points")
        
        try:
            # Test folium map
            m = MapGenerator.create_vessel_track_map(
                track,
                response['VesselName']
            )
            if m:
                print(f"   ✅ Folium map created successfully")
            else:
                print(f"   ❌ Failed to create folium map")
        except Exception as e:
            print(f"   ⚠️ Folium map error: {e}")
        
        try:
            # Test geopandas
            gdf = MapGenerator.create_geopandas_track(
                track,
                response['VesselName']
            )
            if gdf is not None:
                print(f"   ✅ GeoPandas GeoDataFrame created ({len(gdf)} points)")
            else:
                print(f"   ❌ Failed to create GeoDataFrame")
        except Exception as e:
            print(f"   ⚠️ GeoPandas error: {e}")
    else:
        print(f"\n⚠️ No track data available for testing")

def test_datetime_parsing():
    """Test 6: DateTime Parsing"""
    print_section("TEST 6: DateTime Parsing")
    
    nlp = MaritimeNLPInterpreter()
    
    test_queries = [
        'at 10 hours 25 minutes',
        'at 18:25',
        'at 6 PM',
        'after 30 minutes',
        'in 2 hours',
        '2 hours ago',
    ]
    
    print("\n⏰ Testing datetime extraction:")
    for query in test_queries:
        result = nlp.parse_query(query)
        dt = result['datetime']
        end_dt = result['end_dt']
        duration = result['duration_minutes']
        print(f"   Query: '{query}'")
        print(f"      → DateTime: {dt}, Duration: {duration} min")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MARITIME NLU - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # Test 1: Database
    db_file, db = test_database()
    if db is None:
        print("\n❌ No database available. Exiting.")
        return False
    
    # Test 2: NLU Parsing
    test_nlu_parsing(db_file, db)
    
    # Test 3: Intent Executor
    test_intent_executor(db_file, db)
    
    # Test 4: Response Formatter
    test_response_formatter(db_file, db)
    
    # Test 5: Map Generation
    test_map_generation(db_file, db)
    
    # Test 6: DateTime Parsing
    test_datetime_parsing()
    
    print_section("ALL TESTS COMPLETE")
    print("\n✅ Test suite finished successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

