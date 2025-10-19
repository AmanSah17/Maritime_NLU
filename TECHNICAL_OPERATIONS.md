# Maritime NLU - Technical Operations Guide

## 🔍 Detailed Component Operations

### 1. NLU Interpreter - Detailed Flow

#### Intent Detection:
```python
intent_keywords = {
    "show": ["show", "display", "find", "locate", "fetch", "retrieve", "where"],
    "predict": ["predict", "forecast", "estimate", "project"],
    "verify": ["check", "validate", "verify", "compare", "confirm", "consistent"],
}
```
- Keyword matching (case-insensitive)
- Predictive phrasing: "where will X be" → PREDICT
- Relative time patterns: "after 30 minutes" → PREDICT

#### Vessel Name Extraction (Priority Order):
1. **PhraseMatcher** (if vessel_list provided) - Fast multi-word matching
2. **Exact Regex Match** - Whole-word boundary matching
3. **spaCy NER** - ORG/PRODUCT entity recognition
4. **Fuzzy Matching** - RapidFuzz (score >80) or difflib fallback

#### DateTime Extraction (Layered Approach):
1. **spaCy NER** - Extract DATE/TIME entities
2. **dateparser** - Parse combined candidate (if available)
3. **dateutil.parser** - Fuzzy parsing with regex assembly
4. **Regex Heuristics:**
   - Full date+time: `\d{1,2}[-/]\d{1,2}[-/]\d{2,4}` + `\d{1,2}(:\d{2})?\s*(am|pm)`
   - Time-only: `\d{1,2}(:\d{2})?\s*(am|pm)` → normalized to HH:MM:SS
   - Duration: `\d+ hours? \d+ minutes?` → PT format or time-of-day
   - Partial date: `\d{1,2}\s+(jan|feb|...)\w*` → attach midnight

#### End DateTime Computation:
- **Full date+time found** → Use as end_dt
- **Time-only found** → Attach today's date (UTC)
- **Relative phrase** ("in 30 minutes", "2 hours ago") → Compute from now
- **Duration-only** ("for 2 hours") → Return duration_minutes, no end_dt
- **Partial date** ("Jan 5") → Attach midnight

**Output Structure:**
```json
{
  "raw": "original query",
  "intent": "SHOW|PREDICT|VERIFY",
  "vessel_name": "vessel name or null",
  "time_horizon": "after 30 minutes or null",
  "datetime": "HH:MM:SS or YYYY-MM-DD HH:MM:SS or null",
  "end_dt": "YYYY-MM-DD HH:MM:SS or null",
  "duration_minutes": 30 or null,
  "identifiers": {
    "mmsi": "9-digit or null",
    "imo": "7-digit or null",
    "call_sign": "3-7 alphanumeric or null"
  }
}
```

---

### 2. Database Handler - Query Patterns

#### Connection Strategy:
```python
# Preferred: SQLAlchemy with connection pooling
engine = create_engine("sqlite:///db.db", 
                       connect_args={"check_same_thread": False},
                       pool_pre_ping=True)

# Fallback: Direct sqlite3
conn = sqlite3.connect(db_path, check_same_thread=False)
```

#### Key Query Patterns:

**Fetch Last Position:**
```sql
SELECT * FROM vessel_data
WHERE VesselName = ? AND BaseDateTime <= ?
ORDER BY BaseDateTime DESC
LIMIT 1;
```

**Fetch Track (Recent Points):**
```sql
SELECT * FROM vessel_data
WHERE VesselName = ? AND BaseDateTime <= ?
ORDER BY BaseDateTime ASC
LIMIT ?;
```

**Time Range Query:**
```sql
SELECT * FROM vessel_data
WHERE BaseDateTime BETWEEN ? AND ?
ORDER BY BaseDateTime ASC
LIMIT ?;
```

**Prefix Search (Efficient):**
```sql
SELECT DISTINCT VesselName FROM vessel_data
WHERE LOWER(VesselName) LIKE ? 
ORDER BY VesselName ASC 
LIMIT ?;
```

#### Performance Optimizations:
- Indexes on MMSI and BaseDateTime
- WAL mode: `PRAGMA journal_mode=WAL;`
- Synchronous mode: `PRAGMA synchronous=NORMAL;`
- Prefix search avoids loading all names

---

### 3. Intent Executor - Business Logic

#### SHOW Intent Logic:
```
1. Resolve vessel identifier (name or MMSI)
2. If datetime requested:
   a. Try fetch_vessel_by_*_at_or_before(target_dt)
   b. If no result, search ±30 min window
   c. Find nearest point in window
3. Fetch track ending at selected timestamp (10 points)
4. Return: position, SOG, COG, BaseDateTime, track
```

**Fallback Matching Chain:**
- Exact name match
- LIKE wildcard (`%name%`)
- RapidFuzz fuzzy match (score >80)
- difflib fallback (cutoff 0.7)

#### PREDICT Intent Logic:
```
1. Extract time_horizon (e.g., "30 minutes")
2. Fetch last 2 records for vessel
3. Use last record's SOG (knots) + COG (degrees)
4. Dead-reckoning calculation:
   - distance_nm = SOG * (minutes / 60)
   - delta_deg = distance_nm / 60  (1° lat ≈ 60 nm)
   - rad = radians(90 - COG)
   - dlat = delta_deg * sin(rad)
   - dlon = delta_deg * cos(rad) / cos(lat)
   - pred_lat = lat + dlat
   - pred_lon = lon + dlon
5. Return: predicted position, minutes ahead
```

#### VERIFY Intent Logic:
```
1. Fetch last 3 points for vessel
2. For each consecutive pair:
   a. Calculate Haversine distance (nm)
   b. Check for large jumps (>5 nm)
   c. Check for sudden course changes (>90°)
3. Return: verdict (consistent/suspicious), reasons, points
```

**Haversine Formula (nm):**
```python
R_km = 6371.0
dlat = radians(lat2 - lat1)
dlon = radians(lon2 - lon1)
a = sin²(dlat/2) + cos(lat1)*cos(lat2)*sin²(dlon/2)
c = 2*atan2(√a, √(1-a))
dist_km = R_km * c
dist_nm = dist_km / 1.852
```

---

### 4. FastAPI Endpoints - Request/Response

#### POST /query
**Request:**
```json
{"text": "show last position of ABIGAIL at 18:25"}
```

**Response:**
```json
{
  "parsed": {
    "intent": "SHOW",
    "vessel_name": "Abigail",
    "datetime": "18:25:00",
    "end_dt": "2025-10-19 18:25:00",
    "identifiers": {"mmsi": null, "imo": null, "call_sign": null}
  },
  "response": {
    "VesselName": "ABIGAIL",
    "LAT": 40.7128,
    "LON": -74.0060,
    "SOG": 12.5,
    "COG": 180.0,
    "BaseDateTime": "2025-10-19 18:25:00",
    "track": [...]
  }
}
```

#### GET /vessels/search?q=AB&limit=20
**Response:**
```json
{"vessels": ["ABIGAIL", "ABRAHAM", "ABSOLUTE"]}
```

#### GET /admin/describe_vessel?vessel=BRAVA&limit=100
**Response:**
```json
{
  "identifiers": {
    "mmsi": 123456789,
    "call_sign": "BRVA",
    "vessel_name": "+BRAVA"
  },
  "track": [
    {"MMSI": 123456789, "BaseDateTime": "...", "LAT": ..., "LON": ...},
    ...
  ],
  "took_seconds": 0.234
}
```

#### POST /admin/submit_query_job
**Request:**
```json
{"vessel": "BRAVA", "limit": 1000, "end_dt": "2025-10-19T23:59:59"}
```

**Response:**
```json
{"job_id": "uuid-string"}
```

#### GET /admin/job_status/{job_id}
**Response:**
```json
{
  "status": "DONE|RUNNING|PENDING|FAILED",
  "result": {...},
  "error": null
}
```

---

### 5. Streamlit Frontend - State Management

#### Session State Variables:
```python
st.session_state.chat_history  # List of (sender, message) tuples
st.session_state.track_store   # Dict of message_idx → track points
st.session_state.last_bot_response  # Last response dict
st.session_state.map_to_plot   # {"type": "point|track", "vessel": ..., "points": [...]}
```

#### Map Rendering Logic:
1. **Coordinate Extraction:** Extract LAT/LON from response
2. **Time Window Filtering:** Keep points within minutes_window of most recent
3. **Folium Map Creation:** Center on most recent point, zoom=10
4. **Markers:** Blue ship icons for each point
5. **Download:** JSON export of track data

#### Track Plotting:
- Points ordered oldest→newest in DB
- Reversed for display (newest first)
- Time window slider filters by timestamp

---

## 🧪 Testing Strategy

### Unit Tests:
- **test_nlp_datetime.py:** DateTime extraction edge cases
- **test_nlu_and_db.py:** Integration (NLU + DB + Executor)

### E2E Testing:
- **e2e_runner.py:** Start server → run benchmarks → stop server
- **benchmark_api.py:** Performance testing on /admin/describe_vessel

### Test Database:
- **test_db.sqlite:** Small test DB with 5 test vessels
- Created on-the-fly in test setup

---

## 📊 Performance Considerations

### Query Optimization:
- Indexes on MMSI, BaseDateTime
- Prefix search limits results (50 default)
- Time window queries use indexed columns
- Connection pooling via SQLAlchemy

### Scalability:
- WAL mode for concurrent reads
- Thread pool executor (4 workers) for background jobs
- Async support via aiosqlite (optional)
- Lazy loading of vessel names (prefix search)

### Bottlenecks:
- Large dataset scans (mitigated by indexes)
- Fuzzy matching on large vessel lists (RapidFuzz faster than difflib)
- spaCy model loading (cached after first load)

---

## 🐛 Error Handling

### NLU Errors:
- Missing vessel name → return None
- Invalid datetime → try fallback parsers
- No intent detected → return None

### DB Errors:
- Connection failures → fallback to sqlite3
- Query timeouts → return empty DataFrame
- Index creation failures → continue without index

### Intent Executor Errors:
- Empty DataFrame → return "No data found"
- Numeric conversion failures → skip field
- Haversine calculation errors → catch and continue

---

## 🔐 Security Notes

- CORS enabled for localhost (adjust for production)
- No authentication (add for production)
- SQL injection protected (parameterized queries)
- No sensitive data logging (avoid raw AIS in production)

