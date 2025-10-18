import sqlite3
import pandas as pd
import os
from pathlib import Path

from backend.nlu_chatbot.src.app.nlp_interpreter import MaritimeNLPInterpreter
from backend.nlu_chatbot.src.app.db_handler import MaritimeDB
from backend.nlu_chatbot.src.app.intent_executor import IntentExecutor

TEST_DB = Path(__file__).resolve().parent / "test_db.sqlite"


def setup_test_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    rows = []
    for i in range(5):
        rows.append({
            "MMSI": 200000000 + i,
            "BaseDateTime": f"2020-01-03 0{i}:00:00",
            "LAT": 30.0 + i * 0.1,
            "LON": -70.0 + i * 0.1,
            "SOG": 10.0 + i,
            "COG": 90.0 + i,
            "Heading": 100 + i,
            "VesselName": f"UnitTest Vessel {i}",
            "CallSign": f"UT{i:03d}",
            "VesselType": 70,
        })
    df = pd.DataFrame(rows)
    conn = sqlite3.connect(TEST_DB)
    df.to_sql("vessel_data", conn, index=False)
    conn.commit()
    conn.close()


def test_get_unique_vessels_df_and_nlu():
    setup_test_db()
    mdb = MaritimeDB(str(TEST_DB))
    vessels = mdb.get_all_vessel_names()
    assert len(vessels) == 5

    nlp = MaritimeNLPInterpreter(vessel_list=vessels)
    parsed = nlp.parse_query("Show the last known position of UnitTest Vessel 2")
    assert parsed["intent"] == "SHOW"
    assert parsed["vessel_name"] is not None


def test_fetch_vessel_by_name_and_executor():
    mdb = MaritimeDB(str(TEST_DB))
    df = mdb.fetch_vessel_by_name("UnitTest Vessel 3")
    assert not df.empty
    exec = IntentExecutor(mdb)
    parsed = {"intent": "SHOW", "vessel_name": "UnitTest Vessel 3", "identifiers": {}}
    resp = exec.handle(parsed)
    assert isinstance(resp, dict)
    assert resp.get("VesselName") == "UnitTest Vessel 3"


def teardown_module(module):
    try:
        TEST_DB.unlink()
    except Exception:
        pass
