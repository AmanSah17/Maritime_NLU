#!/usr/bin/env python
"""
Test script to diagnose issues with Maritime NLU
"""
import sys
import os
sys.path.insert(0, 'src')

from app.nlp_interpreter import MaritimeNLPInterpreter
from app.db_handler import MaritimeDB
from app.intent_executor import IntentExecutor

def test_database_connection():
    """Test database connectivity"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    for db_file in ['maritime_data.db', 'maritime_sample_0104.db']:
        print(f"\nChecking {db_file}...")
        if os.path.exists(db_file):
            print(f"  ✅ File exists")
            try:
                db = MaritimeDB(db_file)
                vessels = db.get_all_vessel_names()
                print(f"  ✅ Connection successful")
                print(f"  ✅ Found {len(vessels)} unique vessels")
                if vessels:
                    print(f"  Sample: {vessels[:3]}")
                return db_file, db
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"  ❌ File not found")
    
    return None, None

def test_nlu_vessel_extraction(db_file, db):
    """Test NLU vessel name extraction"""
    print("\n" + "="*60)
    print("TEST 2: NLU Vessel Name Extraction")
    print("="*60)
    
    vessels = db.get_all_vessel_names()
    print(f"\nLoaded {len(vessels)} vessels from {db_file}")
    
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    
    test_queries = [
        'show the location of +BRAVA at 10 hours 25 minutes',
        'show +BRAVA',
        'show BRAVA',
        'where is BRAVA',
        'show LAVACA',
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = nlp.parse_query(query)
        print(f"  Intent: {result['intent']}")
        print(f"  Vessel: {result['vessel_name']}")
        print(f"  DateTime: {result['datetime']}")
        print(f"  End DT: {result['end_dt']}")
        print(f"  Duration: {result['duration_minutes']}")

def test_intent_executor(db_file, db):
    """Test intent executor"""
    print("\n" + "="*60)
    print("TEST 3: Intent Executor")
    print("="*60)
    
    vessels = db.get_all_vessel_names()
    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    executor = IntentExecutor(db)
    
    test_queries = [
        'show LAVACA',
        'show TREASURE COAST',
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        parsed = nlp.parse_query(query)
        print(f"  Parsed: {parsed['vessel_name']}")
        
        response = executor.handle(parsed)
        print(f"  Response keys: {list(response.keys())}")
        if 'VesselName' in response:
            print(f"  Vessel: {response['VesselName']}")
            print(f"  Position: {response.get('LAT')}, {response.get('LON')}")
        elif 'message' in response:
            print(f"  Message: {response['message']}")

def test_datetime_parsing():
    """Test datetime parsing"""
    print("\n" + "="*60)
    print("TEST 4: DateTime Parsing")
    print("="*60)
    
    nlp = MaritimeNLPInterpreter()
    
    test_queries = [
        'at 10 hours 25 minutes',
        'at 18:25',
        'at 6 PM',
        'after 30 minutes',
        'in 2 hours',
        '2 hours ago',
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        result = nlp.parse_query(query)
        print(f"  DateTime: {result['datetime']}")
        print(f"  End DT: {result['end_dt']}")
        print(f"  Duration: {result['duration_minutes']}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MARITIME NLU - DIAGNOSTIC TEST SUITE")
    print("="*60)
    
    # Test 1: Database connection
    db_file, db = test_database_connection()
    
    if db is None:
        print("\n❌ No database available. Exiting.")
        sys.exit(1)
    
    # Test 2: NLU vessel extraction
    test_nlu_vessel_extraction(db_file, db)
    
    # Test 3: Intent executor
    test_intent_executor(db_file, db)
    
    # Test 4: DateTime parsing
    test_datetime_parsing()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)

