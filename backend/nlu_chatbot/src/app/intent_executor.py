from .db_handler import MaritimeDB
from typing import Dict
import pandas as pd

class IntentExecutor:
    def __init__(self, db: MaritimeDB):
        self.db = db

    def handle(self, parsed: Dict):
        intent = parsed.get("intent")
        vessel_name = parsed.get("vessel_name")
        identifiers = parsed.get("identifiers", {})

        # Prioritize MMSI if provided
        mmsi = identifiers.get("mmsi")

        df = pd.DataFrame()

        if intent == "SHOW":
            if mmsi:
                df = self.db.fetch_vessel_by_mmsi(int(mmsi))
            elif vessel_name:
                df = self.db.fetch_vessel_by_name(vessel_name)
        elif intent == "VERIFY":
            # Implement logic to check last 3 points
            pass
        elif intent == "PREDICT":
            # Implement prediction based on SOG/COG
            pass

        # Return last known position
        if not df.empty:
            last_row = df.iloc[-1]
            return {
                "VesselName": last_row.VesselName,
                "LAT": last_row.LAT,
                "LON": last_row.LON,
                "SOG": last_row.SOG,
                "COG": last_row.COG,
                "BaseDateTime": last_row.BaseDateTime
            }

        return {"message": "No data found"}
