"""
Create a new sqlite DB from a single AIS .pkl file. This script reads the pickle
(which should contain a DataFrame), filters/renames columns to the expected
schema, and writes to a new SQLite DB with a `vessel_data` table.

Usage:
    python create_db_from_pkl.py --pkl F:\path\to\AIS_2020_01_04.pkl --out F:\path\to\new_db.db
"""
import argparse
import pandas as pd
import sqlite3
from pathlib import Path

EXPECTED_COLS = [
    "MMSI", "BaseDateTime", "LAT", "LON", "SOG", "COG", "Heading", "VesselName", "CallSign", "VesselType"
]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure columns exist and coerce types
    # Lower-case column name mapping
    cols = {c.lower(): c for c in df.columns}
    # create a mapping to expected columns if present
    rename_map = {}
    for ec in EXPECTED_COLS:
        if ec.lower() in cols:
            rename_map[cols[ec.lower()]] = ec
    df = df.rename(columns=rename_map)

    # Keep only expected columns, add missing ones as NA
    for ec in EXPECTED_COLS:
        if ec not in df.columns:
            df[ec] = pd.NA

    # Coerce BaseDateTime to string in ISO format
    try:
        df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], errors='coerce')
        df['BaseDateTime'] = df['BaseDateTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        df['BaseDateTime'] = df['BaseDateTime'].astype(str)

    # Coerce numeric types
    for num in ['MMSI', 'LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']:
        if num in df.columns:
            df[num] = pd.to_numeric(df[num], errors='coerce')

    # Clean VesselName/CallSign
    df['VesselName'] = df['VesselName'].astype(str).str.strip()
    df['CallSign'] = df['CallSign'].astype(str).str.strip()

    return df[EXPECTED_COLS]


def create_db(pkl_path: Path, out_db: Path):
    print(f"Loading {pkl_path}...")
    df = pd.read_pickle(pkl_path)
    print(f"Loaded shape: {df.shape}")
    df2 = normalize_df(df)
    print(f"Normalized shape: {df2.shape}")
    # write to sqlite
    conn = sqlite3.connect(str(out_db))
    df2.to_sql('vessel_data', conn, if_exists='replace', index=False)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);')
    conn.commit()
    conn.close()
    print(f"Wrote DB to {out_db}")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--pkl', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    create_db(Path(args.pkl), Path(args.out))
