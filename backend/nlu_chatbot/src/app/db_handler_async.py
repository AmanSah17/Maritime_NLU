"""
Async Database Handler for Maritime NLU
Provides async access to SQLite database using aiosqlite
"""
import aiosqlite
import pandas as pd
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MaritimeDBAsync:
    """Async wrapper for Maritime database queries"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    async def connect(self):
        """Establish async connection to database"""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            logger.info(f"✅ Async DB connection established: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to async DB: {e}")
            raise
    
    async def close(self):
        """Close async connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Async DB connection closed")
    
    async def get_all_vessel_names(self) -> List[str]:
        """Get all unique vessel names"""
        try:
            query = "SELECT DISTINCT VesselName FROM vessel_data WHERE VesselName IS NOT NULL AND VesselName != 'nan' ORDER BY VesselName"
            async with self.conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error(f"Error fetching vessel names: {e}")
            return []
    
    async def search_vessels_prefix(self, prefix: str, limit: int = 50) -> List[str]:
        """Search vessels by prefix (async)"""
        try:
            prefix_lower = prefix.lower()
            query = """
                SELECT DISTINCT VesselName FROM vessel_data 
                WHERE LOWER(VesselName) LIKE ? 
                AND VesselName IS NOT NULL 
                AND VesselName != 'nan'
                ORDER BY VesselName 
                LIMIT ?
            """
            async with self.conn.execute(query, (f"{prefix_lower}%", limit)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error(f"Error searching vessels: {e}")
            return []
    
    async def fetch_vessel_by_name_at_or_before(
        self, vessel_name: str, target_dt: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch vessel position at or before target datetime (async)"""
        try:
            query = """
                SELECT * FROM vessel_data 
                WHERE VesselName = ? 
                AND BaseDateTime <= ? 
                ORDER BY BaseDateTime DESC 
                LIMIT 1
            """
            async with self.conn.execute(query, (vessel_name, target_dt)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Convert to dict
                    cols = [desc[0] for desc in cursor.description]
                    return dict(zip(cols, row))
                return None
        except Exception as e:
            logger.error(f"Error fetching vessel: {e}")
            return None
    
    async def fetch_track_ending_at(
        self, vessel_name: str, end_dt: str, duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Fetch vessel track ending at datetime (async)"""
        try:
            query = """
                SELECT * FROM vessel_data 
                WHERE VesselName = ? 
                AND BaseDateTime <= ? 
                AND BaseDateTime >= datetime(?, '-' || ? || ' minutes')
                ORDER BY BaseDateTime ASC
            """
            async with self.conn.execute(
                query, (vessel_name, end_dt, end_dt, duration_minutes)
            ) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    cols = [desc[0] for desc in cursor.description]
                    return [dict(zip(cols, row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Error fetching track: {e}")
            return []
    
    async def fetch_by_time_range(
        self, start_dt: str, end_dt: str, limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetch all vessel data in time range (async)"""
        try:
            query = """
                SELECT * FROM vessel_data 
                WHERE BaseDateTime >= ? 
                AND BaseDateTime <= ? 
                ORDER BY BaseDateTime DESC 
                LIMIT ?
            """
            async with self.conn.execute(query, (start_dt, end_dt, limit)) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    cols = [desc[0] for desc in cursor.description]
                    return [dict(zip(cols, row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Error fetching by time range: {e}")
            return []
    
    async def get_unique_vessels_df(self) -> pd.DataFrame:
        """Get unique vessels as DataFrame (async)"""
        try:
            query = """
                SELECT DISTINCT VesselName, COUNT(*) as record_count, 
                       MIN(BaseDateTime) as first_seen, 
                       MAX(BaseDateTime) as last_seen
                FROM vessel_data 
                WHERE VesselName IS NOT NULL AND VesselName != 'nan'
                GROUP BY VesselName 
                ORDER BY record_count DESC
            """
            async with self.conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                data = [dict(zip(cols, row)) for row in rows]
                return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting unique vessels: {e}")
            return pd.DataFrame()

