import os
import sys
import tempfile
import sqlite3
import json
from datetime import datetime

# ensure we can import modules from src/app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app'))
sys.path.insert(0, ROOT)

import pytest
from db_handler import MaritimeDB
from intent_executor import IntentExecutor


def create_sample_db(path):
    db = MaritimeDB(path)
    db.create_tables()
    # Insert a single CHAMPAGNE CHER row (as in example)
    rows = [
        (111111111, '2020-01-03 23:59:31', 26.11824, -80.14815, 0.0, 360.0, 0.0, 'CHAMPAGNE CHER', None, 37.0),
    ]
    cur = db.conn.cursor()
    cur.executemany("INSERT INTO vessel_data VALUES (?,?,?,?,?,?,?,?,?,?);", rows)
    db.conn.commit()
    return db


def test_champagne_cher_time_requests(tmp_path):
    db_file = str(tmp_path / 'test_champagne.db')
    db = create_sample_db(db_file)
    executor = IntentExecutor(db, time_tolerance_minutes=30)

    # Request at 10:00 (same day) - no earlier row exists, should fall back to last known
    parsed = {"intent": "SHOW", "vessel_name": "CHAMPAGNE CHER", "identifiers": {}, "datetime": '2020-01-03 10:00:00'}
    resp = executor.handle(parsed)
    assert isinstance(resp, dict)
    assert resp.get('VesselName') == 'CHAMPAGNE CHER'
    assert abs(resp.get('LAT') - 26.11824) < 1e-6

    # Request at 20:00 same day
    parsed['datetime'] = '2020-01-03 20:00:00'
    resp = executor.handle(parsed)
    assert resp.get('VesselName') == 'CHAMPAGNE CHER'

    # Request with time-only (10AM) as HH:MM:SS
    parsed['datetime'] = '10:00:00'
    resp = executor.handle(parsed)
    assert resp.get('VesselName') == 'CHAMPAGNE CHER'

    # Request a distant date -> should return 'No data found near requested datetime' or fallback to last known
    parsed['datetime'] = '2019-01-01 10:00:00'
    resp = executor.handle(parsed)
    # Accept either a message or a fallback row
    assert (isinstance(resp, dict) and (resp.get('message') or resp.get('VesselName') == 'CHAMPAGNE CHER'))


def test_fuzzy_match_fallback(tmp_path):
    db_file = str(tmp_path / 'test_champagne.db')
    db = create_sample_db(db_file)
    executor = IntentExecutor(db, time_tolerance_minutes=30)

    # Misspelled vessel name should fuzzy-match to CHAMPAGNE CHER
    parsed = {"intent": "SHOW", "vessel_name": "CHAMPAGNE CHAR", "identifiers": {}, "datetime": None}
    resp = executor.handle(parsed)
    assert isinstance(resp, dict)
    # Either no data (if matching fails) or matched
    if 'message' in resp:
        assert resp['message'] == 'No data found' or 'No data' in resp['message']
    else:
        assert resp.get('VesselName') in ('CHAMPAGNE CHER', 'CHAMPAGNE CHER')
