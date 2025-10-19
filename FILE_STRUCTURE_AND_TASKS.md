# Maritime NLU - File Structure & Development Tasks

## 📁 Complete Repository Structure

```
Maritime_NLU/
├── README.md                          # Project overview & quick start
├── PROJECT_SUMMARY.md                 # [NEW] Comprehensive project summary
├── TECHNICAL_OPERATIONS.md            # [NEW] Detailed technical guide
├── FILE_STRUCTURE_AND_TASKS.md        # [NEW] This file
│
├── notebook_01.ipynb                  # Exploratory NLU notebook
│
├── mnlu/                              # Python virtual environment
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── pyvenv.cfg
│
└── backend/
    ├── nlp_interpreter.py             # [LEGACY] Old NLU implementation
    ├── notebook_backend_02.ipynb      # Data import notebook (incomplete)
    │
    ├── backend/                       # [LEGACY] Old backend folder
    │   ├── maritime_data.db           # Database file
    │   └── [lock/log/err files]       # Database artifacts
    │
    └── nlu_chatbot/                   # ⭐ MAIN APPLICATION
        ├── requirements.txt           # Python dependencies
        ├── maritime_data.db           # Main SQLite database
        ├── maritime_data.db-shm       # SQLite WAL files
        ├── maritime_data.db-wal       # SQLite WAL files
        ├── maritime_sample_0104.db    # Sample database for testing
        │
        ├── src/app/                   # ⭐ CORE BACKEND
        │   ├── __init__.py
        │   ├── main.py                # FastAPI server (273 lines)
        │   ├── nlp_interpreter.py     # NLU parsing (358 lines)
        │   ├── db_handler.py          # Database layer (215 lines)
        │   ├── intent_executor.py     # Business logic (280 lines)
        │   ├── main_query_engine.py   # [UNUSED] Alternative query engine
        │   └── run_e2e.py             # [UNUSED] E2E runner
        │
        ├── frontend/                  # ⭐ STREAMLIT UI
        │   ├── app.py                 # Main Streamlit app (233 lines)
        │   ├── pages/                 # [EMPTY] Multi-page support
        │   ├── package-lock.json      # [LEGACY] Node.js lock file
        │   └── __pycache__/
        │
        ├── tests/                     # ⭐ TEST SUITE
        │   ├── test_nlp_datetime.py   # NLU datetime tests (32 lines)
        │   ├── test_nlu_and_db.py     # Integration tests (65 lines)
        │   ├── test_champagne_cher.py # [UNUSED] Specific vessel test
        │   ├── test_db.sqlite         # Test database
        │   └── __pycache__/
        │
        └── tools/                     # ⭐ UTILITY SCRIPTS
            ├── create_db_from_pkl.py          # Convert pickle → SQLite (76 lines)
            ├── create_sample_db_from_pkl.py   # Create sample DB
            ├── import_pkls_to_db.py           # Batch import pickles
            ├── verify_db_import.py            # Validate import
            ├── benchmark_api.py               # Performance testing (33 lines)
            ├── e2e_runner.py                  # E2E test runner (47 lines)
            ├── start_uvicorn_with_db.bat      # Windows batch script
            └── __pycache__/
```

---

## 📊 File Operations Summary

### Core Application Files (1,161 lines total)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `main.py` | 273 | FastAPI server, endpoints, job management | ✅ Active |
| `nlp_interpreter.py` | 358 | NLU parsing, intent/entity extraction | ✅ Active |
| `db_handler.py` | 215 | SQLite queries, pandas DataFrames | ✅ Active |
| `intent_executor.py` | 280 | SHOW/PREDICT/VERIFY business logic | ✅ Active |
| `frontend/app.py` | 233 | Streamlit UI, chat, mapping | ✅ Active |

### Test Files (97 lines total)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `test_nlp_datetime.py` | 32 | DateTime extraction tests | ✅ Active |
| `test_nlu_and_db.py` | 65 | Integration tests | ✅ Active |

### Tool Scripts (156 lines total)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `create_db_from_pkl.py` | 76 | Pickle → SQLite conversion | ✅ Active |
| `benchmark_api.py` | 33 | API performance testing | ✅ Active |
| `e2e_runner.py` | 47 | End-to-end test runner | ✅ Active |

### Legacy/Unused Files

| File | Purpose | Status |
|------|---------|--------|
| `backend/nlp_interpreter.py` | Old NLU implementation | ⚠️ Legacy |
| `main_query_engine.py` | Alternative query engine | ⚠️ Unused |
| `run_e2e.py` | E2E runner (duplicate) | ⚠️ Unused |
| `test_champagne_cher.py` | Specific vessel test | ⚠️ Unused |
| `notebook_backend_02.ipynb` | Data import notebook | ⚠️ Incomplete |

---

## 🎯 Development Tasks & Roadmap

### Phase 1: Foundation (✅ COMPLETE)
- [x] NLU interpreter with intent/entity extraction
- [x] SQLite database layer with pandas integration
- [x] Intent executor (SHOW/PREDICT/VERIFY)
- [x] FastAPI backend with REST endpoints
- [x] Streamlit frontend with mapping
- [x] Unit tests for NLU and DB
- [x] Data import tools

### Phase 2: Enhancement (⏳ PLANNED)
- [ ] **Expand NLU Intents:**
  - [ ] ALERT intent (notify on anomalies)
  - [ ] COMPARE intent (compare two vessels)
  - [ ] ANALYZE intent (statistical analysis)
  - [ ] ROUTE intent (suggest optimal route)

- [ ] **Improve Matching:**
  - [ ] Phonetic matching (Soundex/Metaphone)
  - [ ] Abbreviation expansion (MSC → Mediterranean Shipping Company)
  - [ ] Typo correction (Levenshtein distance)

- [ ] **Performance Optimization:**
  - [ ] Query result caching (Redis)
  - [ ] Batch query optimization
  - [ ] Database partitioning by date
  - [ ] Async query execution

- [ ] **Frontend Enhancements:**
  - [ ] Multi-vessel comparison view
  - [ ] Historical track animation
  - [ ] Real-time alerts dashboard
  - [ ] Export to CSV/GeoJSON

### Phase 3: ML/Prediction (⏳ PLANNED)
- [ ] **LSTM Trajectory Prediction:**
  - [ ] Data preparation (sequence assembly)
  - [ ] Model training (encoder-decoder)
  - [ ] Model evaluation (Haversine error)
  - [ ] FastAPI `/predict` endpoint
  - [ ] Per-vessel model management

- [ ] **Anomaly Detection:**
  - [ ] Isolation Forest for outlier detection
  - [ ] Sudden course/speed changes
  - [ ] Geofence violations
  - [ ] Port dwell time analysis

### Phase 4: Production (⏳ PLANNED)
- [ ] **Deployment:**
  - [ ] Docker containerization
  - [ ] Kubernetes orchestration
  - [ ] Cloud deployment (AWS/GCP/Azure)
  - [ ] CI/CD pipeline (GitHub Actions)

- [ ] **Monitoring & Logging:**
  - [ ] Structured logging (JSON)
  - [ ] Metrics collection (Prometheus)
  - [ ] Error tracking (Sentry)
  - [ ] Performance monitoring

- [ ] **Security:**
  - [ ] Authentication (OAuth2/JWT)
  - [ ] Authorization (role-based access)
  - [ ] API rate limiting
  - [ ] Data encryption (TLS)

- [ ] **Documentation:**
  - [ ] API documentation (Swagger/OpenAPI)
  - [ ] Architecture diagrams
  - [ ] Deployment guide
  - [ ] User manual

### Phase 5: Advanced Features (⏳ FUTURE)
- [ ] **Real-time Processing:**
  - [ ] Kafka/RabbitMQ integration
  - [ ] Stream processing (Flink/Spark)
  - [ ] Live vessel tracking

- [ ] **Advanced Analytics:**
  - [ ] Port congestion analysis
  - [ ] Shipping lane optimization
  - [ ] Fuel consumption estimation
  - [ ] Emissions tracking

- [ ] **Integration:**
  - [ ] Weather API integration
  - [ ] Port information API
  - [ ] Vessel registry API
  - [ ] Compliance/sanctions checking

---

## 🔧 Known Issues & TODOs

### Code Quality:
- [ ] Remove duplicate `return identifiers` in `nlp_interpreter.py` (line 357)
- [ ] Add missing `timedelta` import in `nlp_interpreter.py` (used in line 226)
- [ ] Consolidate legacy files (backend/nlp_interpreter.py)
- [ ] Add type hints to all functions
- [ ] Add docstrings to all classes/methods

### Testing:
- [ ] Increase test coverage (currently ~30%)
- [ ] Add integration tests for all endpoints
- [ ] Add performance benchmarks
- [ ] Add stress testing

### Documentation:
- [ ] Add API documentation (Swagger)
- [ ] Add architecture diagrams
- [ ] Add deployment guide
- [ ] Add troubleshooting guide

### Performance:
- [ ] Optimize datetime parsing (currently slow)
- [ ] Add query result caching
- [ ] Optimize fuzzy matching
- [ ] Profile memory usage

---

## 🚀 Quick Development Commands

### Setup:
```bash
cd backend\nlu_chatbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run Backend:
```bash
cd src\app
uvicorn main:app --reload --port 8000
```

### Run Frontend:
```bash
cd frontend
streamlit run app.py
```

### Run Tests:
```bash
$env:PYTHONPATH='src'
python -m pytest -v
```

### Run Benchmarks:
```bash
python tools\e2e_runner.py
```

### Create DB from Pickle:
```bash
python tools\create_db_from_pkl.py --pkl path\to\AIS_2020_01_03.pkl --out maritime_data.db
```

---

## 📋 Configuration Files

### requirements.txt
```
fastapi
uvicorn
streamlit
pandas
numpy
folium
streamlit-folium
rapidfuzz
streamlit-aggrid
```

### Environment Variables
- `BACKEND_DB_PATH` - Override default database path
- `PYTHONPATH` - Set to `src` for test imports

### Database Configuration
- Default: `backend/nlu_chatbot/maritime_data.db`
- WAL mode enabled for concurrent reads
- Indexes on MMSI and BaseDateTime

