import sqlite3
import pandas as pd
from typing import List, Optional
import sqlalchemy
import aiosqlite


class MaritimeDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Prefer SQLAlchemy engine for connection pooling when available
        try:
            from sqlalchemy import create_engine
            # Use check_same_thread via connect_args for sqlite
            self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, pool_pre_ping=True)
            self.conn = None
        except Exception:
            self.engine = None
            # synchronous fallback connection used by legacy codepaths
            self.conn = sqlite3.connect(db_path, check_same_thread=False)

    # --- Async helpers (useful for FastAPI endpoints to avoid blocking) ---
    async def async_fetch(self, query: str, params: tuple = (), limit: Optional[int] = None) -> pd.DataFrame:
        try:
            import aiosqlite
        except Exception:
            # fallback to sync call if aiosqlite not available
            if self.engine is not None:
                return pd.read_sql_query(query, con=self.engine, params=params)
            return pd.read_sql_query(query, self.conn, params=params)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if limit is not None:
                # append limit if not present
                if "LIMIT" not in query.upper():
                    query = query.rstrip("; ") + f" LIMIT {limit};"
            async with db.execute(query, params) as cur:
                cols = [c[0] for c in cur.description]
                rows = await cur.fetchall()
                return pd.DataFrame([dict(zip(cols, r)) for r in rows])

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
        # Create table using engine if available otherwise via sqlite3
        if self.engine is not None:
            from sqlalchemy import text
            with self.engine.begin() as conn:
                conn.execute(text(query))
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);"))
                except Exception:
                    pass
            # Try to set pragmatic PRAGMAs for better concurrent reads on sqlite
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("PRAGMA journal_mode=WAL;"))
                    conn.execute(text("PRAGMA synchronous=NORMAL;"))
            except Exception:
                pass
        else:
            self.conn.execute(query)
            # create helpful indexes for large datasets
            try:
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);")
                self.conn.commit()
            except Exception:
                # if index creation fails, continue without raising (admin can create later)
                pass

    def get_all_vessel_names(self) -> List[str]:
        query = "SELECT DISTINCT VesselName FROM vessel_data WHERE VesselName IS NOT NULL;"
        if self.engine is not None:
            df = pd.read_sql_query(query, con=self.engine)
        else:
            df = pd.read_sql_query(query, self.conn)
        # return cleaned list
        return df['VesselName'].astype(str).str.strip().tolist()

    def search_vessels_prefix(self, prefix: str, limit: int = 50) -> List[str]:
        """Return up to `limit` vessel names matching the given prefix (case-insensitive).
        This avoids loading all vessel names at once for large DBs.
        """
        pattern = prefix.strip().lower() + "%"
        query = "SELECT DISTINCT VesselName FROM vessel_data WHERE LOWER(VesselName) LIKE ? ORDER BY VesselName ASC LIMIT ?;"
        if self.engine is not None:
            df = pd.read_sql_query(query, con=self.engine, params=(pattern, limit))
        else:
            df = pd.read_sql_query(query, self.conn, params=(pattern, limit))
        return df['VesselName'].astype(str).str.strip().tolist()

    def get_unique_vessels_df(self) -> pd.DataFrame:
        """Return a DataFrame with distinct VesselName values (cleaned)."""
        query = "SELECT DISTINCT VesselName FROM vessel_data WHERE VesselName IS NOT NULL;"
        if self.engine is not None:
            df = pd.read_sql_query(query, con=self.engine)
        else:
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
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(vessel_name_pattern, limit))
        return pd.read_sql_query(query, self.conn, params=(vessel_name_pattern, limit))

    def fetch_vessel_by_name_at_or_before(self, vessel_name: str, target_dt: str) -> pd.DataFrame:
        """Return the single row for vessel_name with BaseDateTime <= target_dt ordered by BaseDateTime DESC limit 1"""
        query = """
        SELECT * FROM vessel_data
        WHERE VesselName = ? AND BaseDateTime <= ?
        ORDER BY BaseDateTime DESC
        LIMIT 1;
        """
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(vessel_name, target_dt))
        return pd.read_sql_query(query, self.conn, params=(vessel_name, target_dt))

    def fetch_vessel_by_mmsi_at_or_before(self, mmsi: int, target_dt: str) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE MMSI = ? AND BaseDateTime <= ?
        ORDER BY BaseDateTime DESC
        LIMIT 1;
        """
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(int(mmsi), target_dt))
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
            if self.engine is not None:
                return pd.read_sql_query(query, con=self.engine, params=(vessel_name, end_dt, limit))
            return pd.read_sql_query(query, self.conn, params=(vessel_name, end_dt, limit))
        elif mmsi:
            query = """
            SELECT * FROM vessel_data
            WHERE MMSI = ? AND BaseDateTime <= ?
            ORDER BY BaseDateTime ASC
            LIMIT ?;
            """
            if self.engine is not None:
                return pd.read_sql_query(query, con=self.engine, params=(int(mmsi), end_dt, limit))
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
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(vessel_name, limit))
        return pd.read_sql_query(query, self.conn, params=(vessel_name, limit))

    def fetch_vessel_by_mmsi(self, mmsi: int, limit: int = 1000) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE MMSI = ?
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(int(mmsi), limit))
        return pd.read_sql_query(query, self.conn, params=(int(mmsi), limit))

    def fetch_by_time_range(self, start: str, end: str, limit: int = 1000) -> pd.DataFrame:
        query = """
        SELECT * FROM vessel_data
        WHERE BaseDateTime BETWEEN ? AND ?
        ORDER BY BaseDateTime ASC
        LIMIT ?;
        """
        if self.engine is not None:
            return pd.read_sql_query(query, con=self.engine, params=(start, end, limit))
        return pd.read_sql_query(query, self.conn, params=(start, end, limit))


