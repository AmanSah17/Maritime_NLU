import sqlite3
import pandas as pd
import os

DB_PATH = r"F:\Maritime_NLU\backend\nlu_chatbot\maritime_data.db"
if not os.path.exists(DB_PATH):
    raise SystemExit(f"DB not found: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
try:
    total = pd.read_sql("SELECT COUNT(*) AS total_rows FROM vessel_data;", conn)
    print("Total rows in vessel_data:", int(total['total_rows'].iloc[0]))
    print('\nTop 10 most recent rows (by BaseDateTime):')
    df = pd.read_sql("SELECT * FROM vessel_data ORDER BY BaseDateTime DESC LIMIT 10;", conn)
    print(df.to_string(index=False))
finally:
    conn.close()
