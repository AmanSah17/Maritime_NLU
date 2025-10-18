import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path

# Ensure local src/app directory on path for imports when running as a script
here = Path(__file__).resolve().parent
if str(here) not in sys.path:
    sys.path.insert(0, str(here))

from db_handler import MaritimeDB
from nlp_interpreter import MaritimeNLPInterpreter
from intent_executor import IntentExecutor

# Create small test DB in temp location
base_dir = Path(__file__).resolve().parents[1]
db_path = base_dir / "maritime_test_e2e.db"
if db_path.exists():
    os.remove(db_path)

# Sample data: 10 unique vessels with MMSI, IMO, etc.
rows = []
for i in range(10):
    mmsi = 100000000 + i
    imo = 9000000 + i
    name = f"Test Vessel {i}"
    lat = 10.0 + i * 0.1
    lon = 20.0 + i * 0.1
    base_dt = f"2020-01-03 0{i}:00:00"
    rows.append({
        "MMSI": mmsi,
        "BaseDateTime": base_dt,
        "LAT": lat,
        "LON": lon,
        "SOG": 12.3 + i,
        "COG": 45.0 + i,
        "Heading": 100 + i,
        "VesselName": name,
        "CallSign": f"CS{i:03d}",
        "VesselType": 70
    })

df = pd.DataFrame(rows)
conn = sqlite3.connect(str(db_path))
df.to_sql("vessel_data", conn, index=False)
conn.commit()
conn.close()

print(f"Created test DB at: {db_path}")

# Attach MaritimeDB to test DB
mdb = MaritimeDB(str(db_path))
print('Row count:', int(pd.read_sql_query('SELECT COUNT(*) as c FROM vessel_data', mdb.conn)['c'].iloc[0]))

vessels = mdb.get_all_vessel_names()
nlp = MaritimeNLPInterpreter(vessel_list=vessels)
exec = IntentExecutor(mdb)

# Create sample natural language queries mixing vessels and identifiers
queries = []
for i in range(10):
    queries.append(f"Show the last known position of Test Vessel {i}.")
    queries.append(f"Find MMSI {100000000 + i} for vessel.")
    queries.append(f"Where will Test Vessel {i} be after 30 minutes?")

for q in queries:
    parsed = nlp.parse_query(q)
    resp = exec.handle(parsed)
    print('\nQuery:', q)
    print('Parsed:', parsed)
    print('Response:', resp)

# Cleanup test DB
try:
    mdb.conn.close()
except Exception:
    pass

print('E2E run complete.')
