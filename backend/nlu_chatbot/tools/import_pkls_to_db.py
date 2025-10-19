"""
Script: import_pkls_to_db.py

Loads AIS .pkl files, filters/cleans columns and appends to the backend SQLite DB used by the app:
  backend/nlu_chatbot/maritime_data.db

Safety:
 - Creates a timestamped backup copy of the DB before writing.
 - Performs a dry-run mode to report counts without writing.
 - Only writes to the target DB path inside backend/nlu_chatbot to avoid accidental writes.

Usage:
    python import_pkls_to_db.py --files "F:\\PyTorch_GPU\\...\\AIS_2020_01_03.pkl" "..." --db-path "F:\\Maritime_NLU\\backend\\nlu_chatbot\\maritime_data.db" --commit

"""
from __future__ import annotations
import argparse
import os
import shutil
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List

REQUIRED_COLUMNS = [
    "MMSI",
    "BaseDateTime",
    "LAT",
    "LON",
    "SOG",
    "COG",
    "Heading",
    "VesselName",
    "CallSign",
    "VesselType",
]


def load_and_clean(pkl_path: str) -> pd.DataFrame:
    print(f"Loading: {pkl_path}")
    df = pd.read_pickle(pkl_path)
    # keep rows with VesselName present
    df = df[df["VesselName"].notna()]
    # keep required columns; if missing, create with NaNs
    for c in REQUIRED_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[REQUIRED_COLUMNS]
    # ensure datetime strings are normalized
    if not pd.api.types.is_datetime64_any_dtype(df["BaseDateTime"]):
        try:
            df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"])
        except Exception:
            # try parsing loosely
            df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"], errors="coerce")
    # drop rows with invalid datetimes
    df = df[df["BaseDateTime"].notna()].copy()
    # normalize format
    df["BaseDateTime"] = df["BaseDateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    # sort
    df = df.sort_values(by=["MMSI", "BaseDateTime"]).reset_index(drop=True)
    print(f"  -> rows after clean: {len(df)}")
    return df


def backup_db(db_path: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = f"{db_path}.{ts}.bak"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created at: {backup_path}")
    return backup_path


def append_to_db(db_path: str, df: pd.DataFrame, table_name: str = "vessel_data") -> None:
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="append", index=False)
    finally:
        conn.close()


def main(file_list: List[str], db_path: str, commit: bool = False):
    # safety: ensure target DB is inside backend/nlu_chatbot
    db_path = os.path.abspath(db_path)
    if "backend\\nlu_chatbot" not in db_path.replace("/", "\\"):
        raise SystemExit("Refusing to write to a DB outside backend/nlu_chatbot (safety check)")

    total_rows = 0
    frames = []
    for p in file_list:
        if not os.path.exists(p):
            print(f"File not found: {p}")
            continue
        df = load_and_clean(p)
        frames.append(df)
        total_rows += len(df)

    if not frames:
        print("No dataframes loaded; exiting.")
        return

    combined = pd.concat(frames, ignore_index=True)
    print(f"Total rows ready to insert: {len(combined)}")

    if not commit:
        print("DRY RUN: no DB changes will be made. Rerun with --commit to apply changes.")
        return

    # ensure DB exists
    if not os.path.exists(db_path):
        print(f"DB not found, creating new DB at {db_path}")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # create empty DB with schema
        conn = sqlite3.connect(db_path)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS vessel_data (
            MMSI INTEGER,
            BaseDateTime TEXT,
            LAT REAL,
            LON REAL,
            SOG REAL,
            COG REAL,
            Heading REAL,
            VesselName TEXT,
            CallSign TEXT,
            VesselType REAL
        );
        """
        conn.execute(create_table_query)
        conn.commit()
        conn.close()

    # backup before writing
    backup_db(db_path)

    # append in chunks to avoid memory pressure
    chunk_size = 100_000
    for i in range(0, len(combined), chunk_size):
        sub = combined.iloc[i : i + chunk_size]
        append_to_db(db_path, sub)
        print(f"Inserted rows {i:,} – {min(i+chunk_size, len(combined)):,}")

    print("✅ Completed commit to DB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True, help="List of .pkl files to load")
    parser.add_argument("--db-path", required=False, default=r"F:\\Maritime_NLU\\backend\\nlu_chatbot\\maritime_data.db")
    parser.add_argument("--commit", action="store_true", help="Apply changes to DB")
    args = parser.parse_args()
    main(args.files, args.db_path, commit=args.commit)
