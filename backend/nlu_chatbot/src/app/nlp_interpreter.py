import spacy
from spacy.matcher import Matcher, PhraseMatcher
import re
from typing import List, Dict, Optional



class MaritimeNLPInterpreter:
    def __init__(self, vessel_list: Optional[List[str]] = None):
        self.vessel_list = [v.lower() for v in vessel_list] if vessel_list else []
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        # Use PhraseMatcher for fast multi-word vessel matching when vessel list is large
        self.phrase_matcher = None
        if self.vessel_list:
            try:
                self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
                patterns = [self.nlp.make_doc(v) for v in self.vessel_list if v]
                # add all under a single label
                self.phrase_matcher.add("VESSEL_PHRASES", patterns)
            except Exception:
                self.phrase_matcher = None

        self._register_patterns()
        self.intent_keywords = {
            "show": ["show", "display", "find", "locate", "fetch", "retrieve"],
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
        doc = self.nlp(text.lower())
        parsed = {
            "intent": self._extract_intent(text.lower()),
            "vessel_name": self._extract_vessel_name(text.lower()),
            "time_horizon": self._extract_time_horizon(doc),
            "identifiers": self._extract_identifiers(text.lower()),
        }
        return parsed

    def _extract_intent(self, text_lower: str) -> Optional[str]:
        # simple keyword mapping first
        for intent, words in self.intent_keywords.items():
            if any(word in text_lower for word in words):
                return intent.upper()

        # detect predictive phrasing like "where will X be" or "after 30 minutes"
        if "where will" in text_lower or re.search(r"after\s+\d+\s+(minutes|minute|hours|hour)", text_lower):
            return "PREDICT"

        # fallback
        return None

    def _extract_vessel_name(self, text_lower: str) -> Optional[str]:
        import re

        # 1) If we have a PhraseMatcher, use it for fast, accurate matching
        if self.phrase_matcher is not None:
            try:
                doc = self.nlp(text_lower)
                matches = self.phrase_matcher(doc)
                if matches:
                    # return longest match (by length)
                    best = max((doc[start:end].text for _, start, end in matches), key=len)
                    return best.title()
            except Exception:
                pass

        # 2) Try exact vessel-list matches using whole-word matching (fallback)
        for vessel in sorted(self.vessel_list, key=len, reverse=True):
            if not vessel:
                continue
            pattern = r"\b" + re.escape(vessel.lower()) + r"\b"
            if re.search(pattern, text_lower):
                return vessel.title()

        # 3) Fallback to spaCy NER for ORG/PRODUCT
        try:
            doc = self.nlp(text_lower)
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"]:
                    return ent.text.title()
        except Exception:
            pass

        return None

    def _extract_time_horizon(self, doc) -> Optional[str]:
        matches = self.matcher(doc)
        for _, start, end in matches:
            return doc[start:end].text
        return None

    def _extract_identifiers(self, text_lower: str) -> Dict[str, Optional[str]]:
        identifiers = {}
        mmsi_match = re.search(r"\b\d{9}\b", text_lower)
        identifiers["mmsi"] = mmsi_match.group() if mmsi_match else None
        imo_match = re.search(r"imo\s*\d+", text_lower)
        identifiers["imo"] = imo_match.group().replace("imo", "").strip() if imo_match else None
        call_match = re.search(r"callsign\s+([a-z0-9]{3,7})", text_lower)
        identifiers["call_sign"] = call_match.group(1).upper() if call_match else None
        return identifiers
