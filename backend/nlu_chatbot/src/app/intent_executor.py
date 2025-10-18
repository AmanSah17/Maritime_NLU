from db_handler import MaritimeDB
from typing import Dict
import pandas as pd
import math
from datetime import datetime, timedelta
from typing import Optional

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

        # If vessel_name looks numeric, treat it as MMSI
        if vessel_name and vessel_name.isdigit() and not mmsi:
            mmsi = vessel_name

        if intent == "SHOW":
            if mmsi:
                df = self.db.fetch_vessel_by_mmsi(int(mmsi), limit=1000)
            elif vessel_name:
                df = self.db.fetch_vessel_by_name(vessel_name, limit=1000)

                # if no exact matches, try a case-insensitive LIKE (wildcard on both sides)
                if df.empty:
                    like_df = self.db.fetch_vessel_by_name_like(f"%{vessel_name}%", limit=1000)
                    if not like_df.empty:
                        df = like_df

                # if still empty, try fuzzy match on vessel list (if rapidfuzz available)
                if df.empty:
                    try:
                        from rapidfuzz import process
                        vessel_candidates = self.db.get_all_vessel_names()
                        best = process.extractOne(vessel_name, vessel_candidates)
                        if best and best[1] > 80:
                            df = self.db.fetch_vessel_by_name(best[0], limit=1000)
                    except Exception:
                        pass

        elif intent == "VERIFY":
            # Verify consistency across last 3 points
            df = pd.DataFrame()
            if mmsi:
                df = self.db.fetch_vessel_by_mmsi(int(mmsi), limit=3)
            elif vessel_name:
                df = self.db.fetch_vessel_by_name(vessel_name, limit=3)

            return self._verify_movement(df)

        elif intent == "PREDICT":
            # Predict position after given time horizon (e.g., 'after 30 minutes')
            # Extract time horizon from parsed (assumed to be like 'after 30 minutes')
            time_horizon = parsed.get("time_horizon")
            minutes = self._parse_minutes(time_horizon) if time_horizon else None

            if mmsi:
                df = self.db.fetch_vessel_by_mmsi(int(mmsi), limit=2)
            elif vessel_name:
                df = self.db.fetch_vessel_by_name(vessel_name, limit=2)

            if minutes is None:
                # default 30 minutes
                minutes = 30

            return self._predict_position(df, minutes)

        # Return last known position
        if not df.empty:
            # Return last known plus last 10 track points (most recent first)
            last_row = df.iloc[-1]
            track = df.tail(10).to_dict(orient='records')
            return {
                "VesselName": last_row.VesselName,
                "LAT": float(last_row.LAT),
                "LON": float(last_row.LON),
                "SOG": float(last_row.SOG),
                "COG": float(last_row.COG),
                "BaseDateTime": last_row.BaseDateTime,
                "track": track[::-1]  # return newest first
            }

        return {"message": "No data found"}

    def _parse_minutes(self, time_horizon: Optional[str]) -> Optional[int]:
        if not time_horizon:
            return None
        import re
        m = re.search(r"(\d+)", time_horizon)
        if m:
            return int(m.group(1))
        return None

    def _predict_position(self, df: pd.DataFrame, minutes: int):
        """Simple dead-reckoning using last known SOG (knots) and COG (degrees).
        SOG is in knots -> convert to nautical miles per minute (1 knot = 1 nm/hr = 1/60 nm/min)
        1 degree latitude ~= 60 nautical miles. For small distances, 1 nm ~= 1/60 degree lat.
        This is a simplification suitable for short horizons.
        """
        if df.empty or len(df) < 1:
            return {"message": "No data to predict"}

        last = df.iloc[-1]
        try:
            sog = float(last.SOG or 0.0)  # knots
            cog = float(last.COG or 0.0)  # degrees
            lat = float(last.LAT)
            lon = float(last.LON)
        except Exception:
            return {"message": "Insufficient numeric data for prediction"}

        # distance in nautical miles = sog * (minutes / 60)
        distance_nm = sog * (minutes / 60.0)

        # convert nm to degrees (approx): 1 degree lat ~ 60 nm
        delta_deg = distance_nm / 60.0

        # Convert bearing to delta lat/lon (simplified):
        rad = math.radians(90 - cog)
        dlat = delta_deg * math.sin(rad)
        dlon = delta_deg * math.cos(rad) / max(math.cos(math.radians(lat)), 0.0001)

        pred_lat = lat + dlat
        pred_lon = lon + dlon

        return {
            "VesselName": last.VesselName,
            "Predicted_LAT": pred_lat,
            "Predicted_LON": pred_lon,
            "MinutesAhead": minutes,
            "BaseDateTime": last.BaseDateTime
        }

    def _verify_movement(self, df: pd.DataFrame):
        """Check last 3 points for sudden jumps or unrealistic turns.
        Return a short verdict and the last points.
        """
        if df.empty or len(df) < 2:
            return {"message": "Not enough data to verify"}

        # compute pairwise distances and bearing changes
        def haversine_nm(lat1, lon1, lat2, lon2):
            # returns distance in nautical miles
            R_km = 6371.0
            import math
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
            c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
            dist_km = R_km * c
            return dist_km / 1.852  # km -> nautical miles

        points = []
        for _, row in df.iterrows():
            points.append((float(row.LAT), float(row.LON), float(row.SOG or 0.0), float(row.COG or 0.0)))

        # analyze distances and speed consistency
        verdict = "consistent"
        reasons = []
        for i in range(1, len(points)):
            lat1, lon1, sog1, cog1 = points[i-1]
            lat2, lon2, sog2, cog2 = points[i]
            dist = haversine_nm(lat1, lon1, lat2, lon2)
            # if a large jump (> 5 nm within short time) mark suspicious
            if dist > 5.0:
                verdict = "suspicious"
                reasons.append(f"Large jump of {dist:.1f} nm between points {i-1} and {i}")

            # large change in heading
            if abs(cog2 - cog1) > 90:
                verdict = "suspicious"
                reasons.append(f"Large course change of {abs(cog2-cog1):.1f} degrees between points {i-1} and {i}")

        return {"verdict": verdict, "reasons": reasons, "points": df.to_dict(orient='records')}
