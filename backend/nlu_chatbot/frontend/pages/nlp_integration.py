"""
Unified Maritime NLP + Admin DataFrame + Map Handler
-----------------------------------------------------
This single script:
 - Loads vessel data from SQLite or CSV
 - Parses natural language queries with MaritimeNLPInterpreter
 - Filters vessel data
 - Optionally returns a map-ready or JSON response
"""

import os
import re
import pandas as pd
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    import dateparser
except Exception:
    dateparser = None

try:
    from dateutil import parser as dateutil_parser
except Exception:
    dateutil_parser = None


# ============================================================
# 1️⃣  NLP INTERPRETER CLASS
# ============================================================

class MaritimeNLPInterpreter:
    def __init__(self, vessel_list: Optional[List[str]] = None):
        self.vessel_list = [v.lower() for v in vessel_list] if vessel_list else []
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = None
        if self.vessel_list:
            try:
                self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
                patterns = [self.nlp.make_doc(v) for v in self.vessel_list if v]
                self.phrase_matcher.add("VESSEL_PHRASES", patterns)
            except Exception:
                self.phrase_matcher = None

        self._register_patterns()
        self.intent_keywords = {
            "show": ["show", "display", "find", "locate", "fetch", "retrieve", "where"],
            "predict": ["predict", "forecast", "estimate", "project"],
            "verify": ["check", "validate", "verify", "compare", "confirm", "consistent"],
        }

    def _register_patterns(self):
        pattern_time = [
            {"LOWER": {"IN": ["after", "in"]}},
            {"LIKE_NUM": True},
            {"LOWER": {"IN": ["minutes", "minute", "hours", "hour"]}},
        ]
        self.matcher.add("TIME_HORIZON", [pattern_time])

    def parse_query(self, text: str) -> Dict[str, Optional[str]]:
        raw = text.strip()
        text_lower = raw.lower()
        doc = self.nlp(text_lower)

        intent = self._extract_intent(text_lower)
        vessel_name = self._extract_vessel_name(text_lower)
        time_horizon = self._extract_time_horizon(doc)
        datetime_extracted = self._extract_datetime(text_lower, doc)
        end_dt, duration_minutes = self._compute_end_dt(text_lower, doc, datetime_extracted, time_horizon)
        identifiers = self._extract_identifiers(text_lower)

        return {
            "raw": raw,
            "intent": intent,
            "vessel_name": vessel_name,
            "time_horizon": time_horizon,
            "datetime": datetime_extracted,
            "end_dt": end_dt,
            "duration_minutes": duration_minutes,
            "identifiers": identifiers,
        }

    # --- (methods shortened for readability, same as yours) ---
    def _extract_intent(self, text_lower: str):
        for intent, words in self.intent_keywords.items():
            if any(w in text_lower for w in words):
                return intent.upper()
        if "where will" in text_lower or re.search(r"after\s+\d+\s+(minutes|hours)", text_lower):
            return "PREDICT"
        return None

    def _extract_vessel_name(self, text_lower: str):
        if self.phrase_matcher:
            doc = self.nlp(text_lower)
            matches = self.phrase_matcher(doc)
            if matches:
                best = max((doc[start:end].text for _, start, end in matches), key=len)
                return best.title()
        for v in self.vessel_list:
            if re.search(rf"\b{re.escape(v.lower())}\b", text_lower):
                return v.title()
        return None

    def _extract_time_horizon(self, doc):
        matches = self.matcher(doc)
        for _, start, end in matches:
            return doc[start:end].text
        return None

    def _extract_datetime(self, text_lower, doc):
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME"):
                try:
                    if dateparser:
                        dt = dateparser.parse(ent.text)
                        if dt:
                            return dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
        return None

    def _compute_end_dt(self, text_lower, doc, datetime_extracted, time_horizon):
        now = datetime.utcnow()
        if datetime_extracted:
            return datetime_extracted, None
        rel_match = re.search(r"\b(in|after|within)\s+(\d+)\s*(minutes|hours)\b", text_lower)
        if rel_match:
            qty = int(rel_match.group(2))
            unit = rel_match.group(3)
            minutes = qty * 60 if "hour" in unit else qty
            return (now + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S"), minutes
        return None, None

    def _extract_identifiers(self, text_lower):
        identifiers = {"mmsi": None, "imo": None, "call_sign": None}
        mmsi = re.search(r"\b(\d{9})\b", text_lower)
        imo = re.search(r"\bimo\s*[:#-]?\s*(\d{7})\b", text_lower, re.I)
        identifiers["mmsi"] = mmsi.group(1) if mmsi else None
        identifiers["imo"] = imo.group(1) if imo else None
        return identifiers


# ============================================================
# 2️⃣  DATA + MAP HANDLER
# ============================================================

class MaritimeDataHandler:
    def __init__(self, db_path: str = "backend/maritime_data.db", vessel_list: Optional[List[str]] = None):
        self.db_path = db_path
        self.interpreter = MaritimeNLPInterpreter(vessel_list=vessel_list)
        self.df = self._load_data()

    def _load_data(self):
        if os.path.exists(self.db_path) and self.db_path.endswith(".db"):
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
            conn.close()
        else:
            csv_path = "backend/vessel_data.csv"
            df = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
        return df

    def handle_query(self, query: str) -> Dict:
        parsed = self.interpreter.parse_query(query)
        vessel_name = parsed["vessel_name"]
        mmsi = parsed["identifiers"].get("mmsi")
        intent = parsed["intent"]

        if self.df.empty:
            return {"error": "No vessel data loaded."}

        df_filtered = self.df.copy()
        if vessel_name:
            df_filtered = df_filtered[df_filtered["vessel_name"].str.lower() == vessel_name.lower()]
        if mmsi:
            df_filtered = df_filtered[df_filtered["mmsi"] == int(mmsi)]

        # limit results for clarity
        df_filtered = df_filtered.head(50)

        return {
            "query": query,
            "parsed": parsed,
            "filtered_count": len(df_filtered),
            "data": df_filtered.to_dict(orient="records"),
        }


# ============================================================
# 3️⃣  MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("🛳️ Maritime NLP + Data Integration System Ready")
    handler = MaritimeDataHandler(
        db_path="backend/maritime_data.db",
        vessel_list=["BRAVA", "ORION", "PACIFIC STAR", "OCEAN PRIDE"]
    )

    while True:
        user_query = input("\nEnter maritime query (or 'exit'): ").strip()
        if user_query.lower() == "exit":
            break

        result = handler.handle_query(user_query)
        print("\n--- NLP Parsed ---")
        print(result["parsed"])
        print("\n--- Filtered Results ---")
        print(f"{result['filtered_count']} records found.")
        if result["filtered_count"]:
            print(pd.DataFrame(result["data"]).head(5))
