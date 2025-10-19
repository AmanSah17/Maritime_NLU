import spacy
from spacy.matcher import Matcher, PhraseMatcher
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    import dateparser
except Exception:
    dateparser = None
try:
    from dateutil import parser as dateutil_parser
except Exception:
    dateutil_parser = None
# Production: enforce spaCy-only NER. Remove optional transformer fallbacks for predictable behavior.
hf_ner = None



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
            "show": ["show", "display", "find", "locate", "fetch", "retrieve","where"],
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
        # existing 'datetime' kept for backward compatibility
        datetime_extracted = self._extract_datetime(text_lower, doc)
        # new richer parsing which attempts to compute an absolute end_dt when possible
        end_dt, duration_minutes = self._compute_end_dt(text_lower, doc, datetime_extracted, time_horizon)
        identifiers = self._extract_identifiers(text_lower)

        # Build a structured JSON-friendly result
        parsed = {
            "raw": raw,
            "intent": intent,
            "vessel_name": vessel_name,
            "time_horizon": time_horizon,
            "datetime": datetime_extracted,
            # end_dt is an ISO datetime string when we can compute an absolute target time
            "end_dt": end_dt,
            # duration_minutes indicates a relative horizon (e.g., in 30 minutes -> 30)
            "duration_minutes": duration_minutes,
            "identifiers": identifiers,
        }

        return parsed

    def _extract_datetime(self, text_lower: str, doc) -> Optional[str]:
        """Try to extract an absolute datetime or time from the text.

        Returns an ISO formatted datetime string when full date+time is found,
        or a time string 'HH:MM:SS' when only time is present. Returns None if nothing found.
        """
        # 1) collect spaCy DATE/TIME entities if any
        parts = []
        try:
            for ent in doc.ents:
                if ent.label_ in ("DATE", "TIME"):
                    parts.append(ent.text)
        except Exception:
            parts = []

        candidate = " ".join(parts).strip()

        # 2) try dateparser if available
        if candidate and dateparser is not None:
            try:
                dt = dateparser.parse(candidate, settings={"PREFER_DATES_FROM": "past"})
                if isinstance(dt, datetime):
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        # 3) fallback to dateutil.parser on combined candidate or on regex-assembled snippets
        text_for_parse = candidate or text_lower
        if dateutil_parser is not None:
            try:
                # Try to find explicit date+time or time-only tokens via regex to avoid wrong defaults
                dt_match = None
                # look for patterns like '8pm on 02 january 2020' or '02 january 2020 8pm'
                # If we find both date and time tokens, let dateutil parse the substring
                date_re = re.search(r"\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b|\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b", text_for_parse, re.I)
                time_re = re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", text_for_parse, re.I)
                if date_re and time_re:
                    sub = f"{date_re.group()} {time_re.group()}"
                    dt_match = dateutil_parser.parse(sub, fuzzy=True)
                else:
                    # if combined candidate exists, try parsing it
                    try:
                        dt_match = dateutil_parser.parse(text_for_parse, fuzzy=True)
                    except Exception:
                        dt_match = None

                if isinstance(dt_match, datetime):
                    return dt_match.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

        # 4) If only a time like '12PM' or '8pm' exists, return normalized time
        # Accept several common formats, e.g. '5 PM', '5pm', '17:00', '5:00 pm', '5 p.m.'
        time_only = re.search(r"\b(\d{1,2})(:(\d{2}))?\s*(?:a\.?m\.?|p\.?m\.?|am|pm)?\b", text_lower, re.I)
        if time_only:
            hour = int(time_only.group(1))
            minute = int(time_only.group(3)) if time_only.group(3) else 0
            # detect am/pm inside the matched text manually
            ampm_match = re.search(r"(a\.?m\.?|p\.?m\.?|am|pm)", time_only.group(0), re.I)
            if ampm_match:
                ampm = ampm_match.group(0).lower()
            else:
                ampm = None

            if ampm and 'p' in ampm and hour != 12:
                hour += 12
            if ampm and 'a' in ampm and hour == 12:
                hour = 0

            # If hour looks like '24' or >23, normalize by modulo
            hour = hour % 24
            return f"{hour:02d}:{minute:02d}:00"

        # 5) duration-like expressions (e.g. '10 hours 25 minutes')
        # If preceded by 'at' treat as time-of-day, otherwise a duration (ISO-ish PT format)
        dur_match = re.search(r"\b(\d{1,2})\s*(?:hours|hour|hrs|hr)\s*(\d{1,2})?\s*(?:minutes|minute|mins|min)?\b", text_lower, re.I)
        if dur_match:
            h = int(dur_match.group(1))
            m = int(dur_match.group(2)) if dur_match.group(2) else 0
            # If phrase contains 'at' preceding it, treat as time-of-day
            prior = re.search(r"\bat\b\s*" + re.escape(dur_match.group(0)), text_lower)
            if prior:
                h = h % 24
                return f"{h:02d}:{m:02d}:00"
            # otherwise return as a duration-like token
            return f"PT{h}H{m}M"

        # No external transformer fallbacks in production; return None if above heuristics didn't find a datetime

        # nothing found
        return None

    def _compute_end_dt(self, text_lower: str, doc, datetime_extracted: Optional[str], time_horizon: Optional[str]):
        """Compute an absolute end datetime (UTC naive string) when possible.

        Returns (end_dt_iso_str_or_None, duration_minutes_or_None).
        Behavior:
          - If the original _extract_datetime returned a full date+time string, prefer it as end_dt.
          - If _extract_datetime returned only a time (HH:MM:SS), attach today's date (UTC) or resolve a date mention nearby.
          - If text includes relative phrases like 'in 30 minutes', 'after 2 hours', '2 hours ago', compute end_dt accordingly.
          - If text includes duration-only phrases like 'for 2 hours' or '10 minutes', return duration_minutes but no end_dt.
          - All returned ISO strings are in '%Y-%m-%d %H:%M:%S' format (UTC naive).
        """
        end_dt = None
        duration_minutes = None
        now = datetime.utcnow()

        # 1) If datetime_extracted looks like a full date+time -> use it
        if datetime_extracted:
            # heuristics: if contains a date portion (year or '-') treat as full
            if re.search(r"\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", str(datetime_extracted)):
                # Normalize to standard format if possible
                try:
                    # attempt dateutil parse for normalization
                    if dateutil_parser is not None:
                        dt = dateutil_parser.parse(datetime_extracted, fuzzy=True)
                        end_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
                        return end_dt, None
                except Exception:
                    pass

        # 2) If datetime_extracted is a time-only string like '18:25:00' attach today's date
        if datetime_extracted and ":" in datetime_extracted and len(datetime_extracted) <= 8:
            try:
                today = now.strftime("%Y-%m-%d")
                end_dt = f"{today} {datetime_extracted}"
                # normalize via dateutil if available
                if dateutil_parser is not None:
                    dt = dateutil_parser.parse(end_dt, fuzzy=True)
                    end_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
                return end_dt, None
            except Exception:
                pass

        # 3) Relative phrases: 'in 30 minutes', 'after 2 hours', '2 hours ago'
        # Look for 'in|after|within X minutes/hours' -> future; 'ago' -> past
        rel_match = re.search(r"\b(in|after|within)\s+(\d+)\s*(minutes|minute|hours|hour)\b", text_lower)
        if rel_match:
            qty = int(rel_match.group(2))
            unit = rel_match.group(3)
            if 'hour' in unit:
                minutes = qty * 60
            else:
                minutes = qty
            duration_minutes = minutes
            end_dt = (now + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
            return end_dt, duration_minutes

        ago_match = re.search(r"(\d+)\s*(minutes|minute|hours|hour)\s+ago\b", text_lower)
        if ago_match:
            qty = int(ago_match.group(1))
            unit = ago_match.group(2)
            if 'hour' in unit:
                minutes = qty * 60
            else:
                minutes = qty
            duration_minutes = -minutes
            end_dt = (now - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
            return end_dt, duration_minutes

        # 4) Duration-only expressions like 'for 2 hours' or 'duration 30 minutes'
        dur_only = re.search(r"\bfor\s+(\d+)\s*(minutes|minute|hours|hour)\b", text_lower)
        if dur_only:
            qty = int(dur_only.group(1))
            unit = dur_only.group(2)
            if 'hour' in unit:
                minutes = qty * 60
            else:
                minutes = qty
            duration_minutes = minutes
            return None, duration_minutes

        # 5) Partial date mention like 'Jan 5' or '5 Jan' without time -> attach midnight
        partial_date = re.search(r"\b(\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2})\b", text_lower, re.I)
        if partial_date:
            try:
                text_date = partial_date.group(0)
                if dateutil_parser is not None:
                    dt = dateutil_parser.parse(text_date, default=now)
                    # if year is missing, dateutil may choose this year; ensure time set to 00:00:00
                    dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_dt = dt.strftime("%Y-%m-%d %H:%M:%S")
                    return end_dt, None
            except Exception:
                pass

        # 6) fallback: if time_horizon looks like 'after 30 minutes' but not caught earlier
        if time_horizon:
            m = re.search(r"(\d+)\s*(minutes|minute|hours|hour)", time_horizon)
            if m:
                qty = int(m.group(1))
                if 'hour' in m.group(2):
                    minutes = qty*60
                else:
                    minutes = qty
                duration_minutes = minutes
                end_dt = (now + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
                return end_dt, duration_minutes

        return None, None

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

        # No external transformer fallbacks - rely on spaCy and vessel list heuristics only

        return None

    def _extract_time_horizon(self, doc) -> Optional[str]:
        matches = self.matcher(doc)
        for _, start, end in matches:
            return doc[start:end].text
        return None

    def _extract_identifiers(self, text_lower: str) -> Dict[str, Optional[str]]:
        identifiers = {}
        # MMSI: exactly 9 digits
        mmsi_match = re.search(r"\b(\d{9})\b", text_lower)
        identifiers["mmsi"] = mmsi_match.group(1) if mmsi_match else None

        # IMO: 7 digits usually; allow formats like 'IMO 1234567' or 'imo:1234567'
        imo_match = re.search(r"\bimo\s*[:#-]?\s*(\d{7})\b", text_lower, re.I)
        identifiers["imo"] = imo_match.group(1) if imo_match else None

        # callsign
        call_match = re.search(r"callsign\s*[:\s]+([A-Z0-9]{3,7})", text_lower, re.I)
        identifiers["call_sign"] = call_match.group(1).upper() if call_match else None

        # If user typed a vessel name followed by a 9-digit token (e.g., '+BRAVA 123456789'), capture that MMSI
        trailing_mmsi = re.search(r"([A-Za-z\+\-\s]+)\s+(\d{9})\b", text_lower)
        if trailing_mmsi and not identifiers["mmsi"]:
            identifiers["mmsi"] = trailing_mmsi.group(2)

        return identifiers
        return identifiers
