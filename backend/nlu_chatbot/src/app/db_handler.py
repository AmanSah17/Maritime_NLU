import sqlite3
import pandas as pd
from typing import List, Optional

class MaritimeDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def create_tables(self):
        query = """
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
        self.conn.execute(query)
        self.conn.commit()

    def get_all_vessel_names(self) -> List[str]:
        query = "SELECT DISTINCT VesselName FROM vessel_data WHERE VesselName IS NOT NULL;"
        df = pd.read_sql_query(query, self.conn)
        # return cleaned list
        return df['VesselName'].astype(str).str.strip().tolist()

    def get_unique_vessels_df(self) -> pd.DataFrame:
        """Return a DataFrame with distinct VesselName values (cleaned)."""
        query = "SELECT DISTINCT VesselName FROM vessel_data WHERE VesselName IS NOT NULL;"
        df = pd.read_sql_query(query, self.conn)
        df['VesselName'] = df['VesselName'].astype(str).str.strip()
        return df.dropna().drop_duplicates().sort_values('VesselName').reset_index(drop=True)

    def fetch_vessel_by_name_like(self, vessel_name_pattern: str, limit: int = 1000) -> pd.DataFrame:
        """Perform a case-insensitive LIKE query on VesselName.
        vessel_name_pattern should include '%' wildcards as needed.
        """
        query = """
        SELECT * FROM vessel_data
        WHERE LOWER(TRIM(VesselName)) LIKE LOWER(TRIM(?))
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        return pd.read_sql_query(query, self.conn, params=(vessel_name_pattern, limit))

    def fetch_vessel_by_name_at_or_before(self, vessel_name: str, target_dt: str) -> pd.DataFrame:
        """Return the single row for vessel_name with BaseDateTime <= target_dt ordered by BaseDateTime DESC limit 1"""
        query = """
        SELECT * FROM vessel_data
        WHERE VesselName = ? AND BaseDateTime <= ?
        ORDER BY BaseDateTime DESC
        LIMIT 1;
        """
        return pd.read_sql_query(query, self.conn, params=(vessel_name, target_dt))

    def fetch_vessel_by_mmsi_at_or_before(self, mmsi: int, target_dt: str) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE MMSI = ? AND BaseDateTime <= ?
        ORDER BY BaseDateTime DESC
        LIMIT 1;
        """
        return pd.read_sql_query(query, self.conn, params=(int(mmsi), target_dt))

    def fetch_track_ending_at(self, vessel_name: str = None, mmsi: int = None, end_dt: str = None, limit: int = 10) -> pd.DataFrame:
        """Return up to `limit` rows for the vessel with BaseDateTime <= end_dt ordered ASC (oldest->newest)
        If vessel_name provided, use it; otherwise use mmsi.
        """
        if vessel_name:
            query = """
            SELECT * FROM vessel_data
            WHERE VesselName = ? AND BaseDateTime <= ?
            ORDER BY BaseDateTime ASC
            LIMIT ?;
            """
            return pd.read_sql_query(query, self.conn, params=(vessel_name, end_dt, limit))
        elif mmsi:
            query = """
            SELECT * FROM vessel_data
            WHERE MMSI = ? AND BaseDateTime <= ?
            ORDER BY BaseDateTime ASC
            LIMIT ?;
            """
            return pd.read_sql_query(query, self.conn, params=(int(mmsi), end_dt, limit))
        else:
            return pd.DataFrame()

    def fetch_vessel_by_name(self, vessel_name: str, limit: int = 1000) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE VesselName = ?
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        return pd.read_sql_query(query, self.conn, params=(vessel_name, limit))

    def fetch_vessel_by_mmsi(self, mmsi: int, limit: int = 1000) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE MMSI = ?
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        return pd.read_sql_query(query, self.conn, params=(int(mmsi), limit))

    def fetch_by_time_range(self, start: str, end: str, limit: int = 1000) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE BaseDateTime BETWEEN ? AND ?
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        return pd.read_sql_query(query, self.conn, params=(start, end, limit))


