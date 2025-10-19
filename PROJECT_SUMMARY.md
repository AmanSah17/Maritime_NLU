# Maritime NLU - Full Stack Project Summary

## 🎯 Project Objective

**Maritime Vessel Monitoring System** - A production-oriented Natural Language Understanding (NLU) and visualization toolkit for maritime Automatic Identification System (AIS) data. The system enables users to query vessel positions, predict trajectories, and verify movement consistency through conversational natural language queries.

**Version:** v0.0.1 (Early Foundation)

---

## 📋 Project Architecture Overview

### Three-Tier Stack:
1. **Backend (FastAPI)** - NLU parsing + database queries
2. **Frontend (Streamlit)** - Conversational UI + interactive mapping
3. **Database (SQLite)** - AIS vessel tracking data

---

## 🔧 Core Components & Operations

### 1. **NLU Interpreter** (`nlp_interpreter.py`)
**Purpose:** Parse natural language queries into structured intent + entities

**Key Operations:**
- **Intent Extraction:** SHOW, PREDICT, VERIFY
- **Vessel Name Matching:** PhraseMatcher (fast) → exact match → fuzzy match (RapidFuzz/difflib)
- **DateTime Extraction:** Multi-layer approach:
  - spaCy NER entities
  - dateparser library (if available)
  - dateutil parser with regex heuristics
  - Time-only patterns (12PM, 18:25, etc.)
- **Identifier Extraction:** MMSI (9 digits), IMO (7 digits), CallSign (3-7 alphanumeric)
- **Time Horizon Parsing:** "after 30 minutes", "in 2 hours", "2 hours ago"
- **End DateTime Computation:** Converts relative times to absolute ISO timestamps

**Supported Query Examples:**
- "Show last position of INS Kolkata"
- "Predict where MSC Flaminia will be after 30 minutes"
- "Check if Ever Given's movement is consistent"
- "Find vessel with MMSI 419999999"

---

### 2. **Database Handler** (`db_handler.py`)
**Purpose:** SQLite access layer with pandas DataFrame returns

**Key Operations:**
- **Table Schema:** `vessel_data` with columns: MMSI, BaseDateTime, LAT, LON, SOG, COG, Heading, VesselName, CallSign, VesselType
- **Indexes:** MMSI, BaseDateTime (for fast lookups)
- **Query Methods:**
  - `get_all_vessel_names()` - Unique vessel list
  - `search_vessels_prefix()` - Fast prefix search (avoids loading all names)
  - `fetch_vessel_by_name_at_or_before()` - Last position at/before timestamp
  - `fetch_vessel_by_mmsi_at_or_before()` - Same but by MMSI
  - `fetch_track_ending_at()` - Recent track points (e.g., last 10 positions)
  - `fetch_by_time_range()` - Time window queries
- **Connection Modes:** SQLAlchemy engine (preferred) or sqlite3 fallback
- **Async Support:** aiosqlite for non-blocking queries

---

### 3. **Intent Executor** (`intent_executor.py`)
**Purpose:** Business logic for handling parsed intents

**Operations by Intent:**

**SHOW Intent:**
- Fetch vessel by name or MMSI
- If datetime requested: find closest record within tolerance window (±30 min default)
- Return: vessel position, SOG, COG, BaseDateTime, recent track (10 points)
- Fallback matching: exact → LIKE wildcard → fuzzy match

**PREDICT Intent:**
- Extract time horizon (e.g., "30 minutes")
- Use last known SOG (knots) + COG (degrees) for dead-reckoning
- Convert: SOG → nautical miles/min → degrees lat/lon
- Apply bearing math: `dlat = delta_deg * sin(bearing)`, `dlon = delta_deg * cos(bearing) / cos(lat)`
- Return: predicted LAT/LON, minutes ahead

**VERIFY Intent:**
- Fetch last 3 points for vessel
- Check for anomalies:
  - Large jumps (>5 nm between consecutive points)
  - Sudden course changes (>90° heading change)
- Return: verdict (consistent/suspicious), reasons, point details

---

### 4. **FastAPI Backend** (`main.py`)
**Purpose:** REST API exposing NLU + DB functionality

**Key Endpoints:**
- `POST /query` - Main NLU query endpoint
  - Input: `{"text": "show last position of ABIGAIL"}`
  - Output: `{"parsed": {...}, "response": {...}}`
- `GET /vessels` - List all unique vessel names
- `GET /vessels/search?q=prefix&limit=50` - Prefix search (server-side)
- `GET /health` - Health check
- `GET /admin/describe_vessel?vessel=NAME&limit=10` - Detailed vessel info + track
- `POST /admin/submit_query_job` - Background job submission
- `GET /admin/job_status/{job_id}` - Poll job status
- `GET /admin/unique_vessels_df` - Admin diagnostics
- `POST /admin/log_search` - Log user searches

**Features:**
- CORS enabled for frontend access
- Thread pool executor for long-running queries
- Optional React static file serving
- Search logging for analytics

---

### 5. **Streamlit Frontend** (`frontend/app.py`)
**Purpose:** Conversational UI + interactive mapping

**Key Features:**
- **Chat Interface:** User input → backend query → bot response
- **Vessel Directory:** Sidebar with prefix search (2+ chars)
- **Interactive Map:** Folium-based visualization
  - Plot single points or tracks
  - Time window filtering (1-120 minutes)
  - Ship icon markers
  - JSON download of track data
- **Last Response Summary:** Human-readable vessel info outside chat
- **Session State Management:** Chat history, track storage, map payloads
- **Track Plotting:** Buttons to visualize vessel movements

---

## 📊 Data Flow

```
User Query (Streamlit)
    ↓
POST /query (FastAPI)
    ↓
NLU Interpreter (parse intent, entities, datetime)
    ↓
Intent Executor (business logic)
    ↓
Database Handler (SQLite queries)
    ↓
Response (JSON: vessel position, track, predictions)
    ↓
Streamlit Frontend (render map, chat, summary)
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE vessel_data (
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
CREATE INDEX idx_vessel_mmsi ON vessel_data(MMSI);
CREATE INDEX idx_vessel_basedatetime ON vessel_data(BaseDateTime);
```

---

## 🛠️ Tools & Utilities

### Data Import Tools:
- **`create_db_from_pkl.py`** - Convert AIS pickle files to SQLite DB
- **`import_pkls_to_db.py`** - Batch import multiple pickle files
- **`create_sample_db_from_pkl.py`** - Create sample DB for testing

### Testing & Benchmarking:
- **`benchmark_api.py`** - Performance testing of API endpoints
- **`e2e_runner.py`** - End-to-end test runner (start server, run benchmarks)
- **`verify_db_import.py`** - Validate DB import integrity

### Test Suites:
- **`test_nlp_datetime.py`** - NLU datetime extraction tests
- **`test_nlu_and_db.py`** - Integration tests (NLU + DB + Intent Executor)

---

## 📦 Dependencies

**Core:**
- fastapi, uvicorn
- streamlit, streamlit-folium, folium
- pandas, numpy
- sqlalchemy, aiosqlite
- spacy (en_core_web_sm model)

**Optional:**
- rapidfuzz (fuzzy matching; falls back to difflib)
- dateparser (advanced datetime parsing)
- python-dateutil (datetime utilities)

---

## 🚀 Quick Start

### Setup:
```bash
cd F:\Maritime_NLU
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\nlu_chatbot\requirements.txt
python -m spacy download en_core_web_sm
```

### Run Backend:
```bash
cd backend\nlu_chatbot\src\app
uvicorn main:app --reload
```

### Run Frontend:
```bash
cd backend\nlu_chatbot\frontend
streamlit run app.py
```

### Run Tests:
```bash
cd backend\nlu_chatbot
$env:PYTHONPATH='F:\Maritime_NLU\backend\nlu_chatbot\src'
python -m pytest -q
```

---

## 🔮 Roadmap - LSTM Vessel Prediction (Future)

**Phase 1: Data Preparation**
- Assemble sequences (last 30 timestamps per vessel)
- Features: lat, lon, SOG, COG, time-deltas, engineered (sine/cosine bearing)
- Normalize per-feature and per-vessel
- Time-based train/val/test split

**Phase 2: Model**
- LSTM/GRU encoder-decoder
- Loss: MSE on coordinates or Haversine distance
- Attention, gradient clipping, early stopping

**Phase 3: Serving**
- Export (TorchScript/ONNX/SavedModel)
- FastAPI `/predict` endpoint

**Phase 4: Evaluation**
- Per-vessel metrics: mean Haversine error, 95th percentile, drift

**Phase 5: Monitoring**
- Track performance, retrain on sliding window

---

## 📝 Key Files Summary

| File | Purpose |
|------|---------|
| `nlp_interpreter.py` | NLU parsing (intent, entities, datetime) |
| `db_handler.py` | SQLite access layer |
| `intent_executor.py` | Business logic (SHOW/PREDICT/VERIFY) |
| `main.py` | FastAPI server + endpoints |
| `frontend/app.py` | Streamlit UI |
| `requirements.txt` | Python dependencies |
| `tests/` | pytest test suites |
| `tools/` | Data import, benchmarking, E2E testing |

---

## ✅ Current Status

- ✅ NLU parsing (intent, entities, datetime extraction)
- ✅ Database queries (vessel lookup, track retrieval)
- ✅ Intent execution (SHOW, PREDICT, VERIFY)
- ✅ FastAPI backend with CORS
- ✅ Streamlit frontend with mapping
- ✅ Unit tests for NLU and DB
- ✅ Data import tools
- ⏳ LSTM prediction (planned)
- ⏳ Advanced analytics (planned)

---

## 🎓 Next Steps for Development

1. **Expand NLU:** Add more intent types (ALERT, COMPARE, ANALYZE)
2. **Improve Matching:** Enhance fuzzy matching for vessel names
3. **Performance:** Add caching, optimize DB queries for large datasets
4. **LSTM Models:** Implement per-vessel trajectory prediction
5. **Monitoring:** Add logging, metrics, alerting
6. **Deployment:** Docker containerization, cloud deployment

