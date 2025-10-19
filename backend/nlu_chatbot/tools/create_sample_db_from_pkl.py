"""
Create a small sampled sqlite DB from a large AIS .pkl file to enable fast local testing.
Default sample size is 100000 rows. Writes to `backend/nlu_chatbot/maritime_sample_0104.db` by default.

Usage:
    python create_sample_db_from_pkl.py --pkl <path> [--out <out_db>] [--sample 100000]
"""
import argparse
import pandas as pd
import sqlite3
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parents[1] / 'maritime_sample_0104.db'

EXPECTED_COLS = [
    "MMSI", "BaseDateTime", "LAT", "LON", "SOG", "COG", "Heading", "VesselName", "CallSign", "VesselType"
]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    rename_map = {}
    for ec in EXPECTED_COLS:
        if ec.lower() in cols:
            rename_map[cols[ec.lower()]] = ec
    df = df.rename(columns=rename_map)
    for ec in EXPECTED_COLS:
        if ec not in df.columns:
            df[ec] = pd.NA
    try:
        df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], errors='coerce')
        df['BaseDateTime'] = df['BaseDateTime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        df['BaseDateTime'] = df['BaseDateTime'].astype(str)
    for num in ['MMSI', 'LAT', 'LON', 'SOG', 'COG', 'Heading', 'VesselType']:
        if num in df.columns:
            df[num] = pd.to_numeric(df[num], errors='coerce')
    df['VesselName'] = df['VesselName'].astype(str).str.strip()
    df['CallSign'] = df['CallSign'].astype(str).str.strip()
    return df[EXPECTED_COLS]


def create_sample(pkl_path: Path, out_db: Path, sample_size: int):
    print(f"Loading {pkl_path} (will sample {sample_size} rows)...")
    # Read in chunks to avoid memory blowup
    df = pd.read_pickle(pkl_path)
    print(f"Loaded shape: {df.shape}")
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
    df2 = normalize_df(df)
    print(f"Normalized shape: {df2.shape}")
    conn = sqlite3.connect(str(out_db))
    df2.to_sql('vessel_data', conn, if_exists='replace', index=False)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);')
    conn.commit()
    conn.close()
    print(f"Wrote sample DB to {out_db}")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--pkl', required=True)
    p.add_argument('--out', default=str(DEFAULT_OUT))
    p.add_argument('--sample', type=int, default=100000)
    args = p.parse_args()
    create_sample(Path(args.pkl), Path(args.out), args.sample)
