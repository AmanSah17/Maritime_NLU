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
        return df['VesselName'].tolist()

    def fetch_vessel_by_name(self, vessel_name: str, limit: int = 1000) -> pd.DataFrame:
        query = f"""
        SELECT * FROM vessel_data
        WHERE VesselName = '{vessel_name}'
        ORDER BY BaseDateTime ASC
        LIMIT {limit};
        """
        return pd.read_sql_query(query, self.conn)

    def fetch_vessel_by_mmsi(self, mmsi: int, limit: int = 1000) -> pd.DataFrame:
        query = f"""
        SELECT * FROM vessel_data
        WHERE MMSI = {mmsi}
        ORDER BY BaseDateTime ASC
        LIMIT {limit};
        """
        return pd.read_sql_query(query, self.conn)

    def fetch_by_time_range(self, start: str, end: str, limit: int = 1000) -> pd.DataFrame:
        query = f"""
        SELECT * FROM vessel_data
        WHERE BaseDateTime BETWEEN '{start}' AND '{end}'
        ORDER BY BaseDateTime ASC
        LIMIT {limit};
        """
        return pd.read_sql_query(query, self.conn)


