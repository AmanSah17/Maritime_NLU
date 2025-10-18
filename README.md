# Maritime NLU — v0.0.1

A production-oriented Natural Language Understanding (NLU) and visualization toolkit for maritime Automatic Identification System (AIS) data. The project provides:

- A robust NLU interpreter (spaCy-based) that extracts user intent, vessel identifiers, and explicit datetimes from free-text queries.
- A FastAPI backend exposing query endpoints to fetch the last-known position, tracks, and metadata for vessels stored in a SQLite database.
- A Streamlit frontend that provides a conversational UI, an interactive map (Folium), and a searchable vessel directory in the sidebar.
- Unit tests (pytest) validating NLU date/time extraction and database query helpers.

This repository is an early, extendable foundation for later per-vessel predictive models (for example LSTM-based trajectory prediction).

---

## Table of contents

- Features
- Architecture
- Quick start
  - Prerequisites
  - Setup (virtualenv / venv)
  - Run backend
  - Run frontend (Streamlit)
- API
- Data & DB
- Testing
- Development notes
- Roadmap (LSTM vessel-wise prediction)
- License

---

## Features

- Intents supported: SHOW (last position / position at time), PREDICT (simple dead-reckoning), VERIFY (sanity checks)
- Robust vessel name matching with fuzzy fallbacks (RapidFuzz optional, difflib fallback)
- Tiered datetime parsing: spaCy entities → dateparser (optional) → dateutil → regex/time-only heuristics
- SQLite-backed queries returning pandas DataFrames for easy analysis
- Streamlit UI with:
  - Conversational chat area
  - Last-response summary outside the chat
  - Interactive Folium map (markers, optional track plotting)
  - Sidebar vessel directory with search + quick-query
- Pytest suite for key NLU and DB behaviors

---

## Architecture

- backend/nlu_chatbot/src/app
  - `nlp_interpreter.py` — NLU parsing and datetime extraction
  - `db_handler.py` — SQLite access helpers returning pandas DataFrames
  - `intent_executor.py` — Business logic for SHOW/PREDICT/VERIFY intents
  - `main.py` — FastAPI application exposing `/query` and `/vessels` endpoints
- backend/nlu_chatbot/frontend
  - `app.py` — Streamlit conversational UI and mapping
- backend/nlu_chatbot/tests
  - pytest test suites validating parsing and DB helpers
- frontend-react/ (optional)
  - React scaffold for a modern web UI (consumes FastAPI endpoints)

---

## Quick start

These instructions assume a Windows environment (PowerShell) and focus on the Streamlit frontend backed by the FastAPI server.

### Prerequisites

- Python 3.8+ (your environment shows 3.13 in a virtualenv — that's fine).
- Git (for cloning and version control).
- Node/npm (only required if you want to build the optional React frontend).

Recommended: create and use a virtual environment.

### Setup (virtualenv)

```powershell
cd F:\Maritime_NLU
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\nlu_chatbot\requirements.txt
# If you don't have a requirements.txt, install core deps:
# pip install fastapi uvicorn[standard] pandas sqlalchemy python-dateutil spacy streamlit folium streamlit-folium pytest
# Optional (improves fuzzy matching): pip install rapidfuzz
```

Note: If `en_core_web_sm` is not installed for spaCy:
```powershell
python -m spacy download en_core_web_sm
```

### Run the backend (FastAPI)

From the backend app folder:

```powershell
cd F:\Maritime_NLU\backend\nlu_chatbot\src\app
# start with auto-reload during development
uvicorn main:app --reload
```

Default: FastAPI serves on http://127.0.0.1:8000

### Run the frontend (Streamlit)

From the Streamlit frontend folder:

```powershell
cd F:\Maritime_NLU\backend\nlu_chatbot\frontend
streamlit run app.py
```

The Streamlit app will call the backend endpoints to fetch vessel lists and perform queries.

---

## API

The FastAPI app exposes two key endpoints used by the frontend:

- POST `/query`
  - Request JSON: {"text": "show last position of ABIGAIL at 18:25"}
  - Response JSON: {"response": { ... parsed response dict ... }}

- GET `/vessels`
  - Response JSON: {"vessels": ["ABIGAIL", "CHAMPAGNE CHER", ... ]}

Check `backend/nlu_chatbot/src/app/main.py` for implementation details and additional endpoints.

---

## Data & DB

- The app uses a SQLite database in the repo (default location: `backend/nlu_chatbot/maritime_data.db`).
- `db_handler.py` provides helper functions that return pandas DataFrames and perform time-aware lookups (fetching the last row at or before a datetime, fetching short tracks ending at a given time, etc.).

Performance note: for larger datasets add an index on `BaseDateTime` (suggested SQL):

```sql
CREATE INDEX IF NOT EXISTS idx_vessel_data_basedatetime ON vessel_data(BaseDateTime);
```

---

## Testing

Run pytest from the backend test folder:

```powershell
cd F:\Maritime_NLU\backend\nlu_chatbot
# Ensure PYTHONPATH contains src if tests import the package-style modules
$env:PYTHONPATH='F:\Maritime_NLU\backend\nlu_chatbot\src'; python -m pytest -q
```

Tests included cover NLU datetime extraction and DB helpers used for SHOW/PREDICT operations.

---

## Development notes

- NLU: `nlp_interpreter.py` uses a layered approach to extract explicit datetimes from text. When dateparser or more advanced libraries are available, it will prefer them; otherwise it falls back to dateutil and regex heuristics.
- Fuzzy matching: RapidFuzz is supported if installed; otherwise difflib's SequenceMatcher is used as a fallback.
- Streamlit: For reliable session-state behavior run the app with `streamlit run app.py`. Importing the module directly may show warnings about session state.
- Logging: For debugging add logging in `main.py`, `db_handler.py`, and `intent_executor.py`. Avoid logging raw AIS messages in production without redaction.

---

## Roadmap — Vessel-wise LSTM prediction (future work)

Planned next steps to add per-vessel sequence-based prediction using LSTM or other time-series models:

1. Data preparation
   - For each MMSI (vessel), assemble sequences of fixed length (e.g., last 30 timestamps) containing features: latitude, longitude, SOG, COG, time-deltas, and engineered features (sine/cosine of bearing, speed-acceleration).
   - Normalize scales per-feature and optionally per-vessel.
   - Split sequences into train/val/test by time (avoid random splits that leak future info).

2. Model
   - Start with a simple LSTM (or GRU) encoder-decoder predicting next K coordinates or delta-lat/delta-lon.
   - Loss: MSE on coordinates or Haversine-distance-based loss.
   - Add attention/clipped gradients and early stopping.

3. Serving
   - Export model (TorchScript, ONNX or SavedModel) and add a FastAPI `/predict` endpoint that accepts recent sequence and returns predicted coordinates and confidence.

4. Evaluation
   - Evaluate per-vessel and overall: mean Haversine error, 95th percentile error, and drift over longer horizons.

5. Monitoring
   - Track model performance per-vessel and retrain on sliding window schedule.

---

## Contributing

- Please open issues for bugs or feature requests.
- Add unit tests for any substantive logic changes.
- Keep commits small and descriptive; use conventional commits if possible.

---

## License

Specify your license here (MIT/Apache-2.0/etc.).

---

If you'd like, I can:
- Add a `requirements.txt` or `pyproject.toml` to the repo (I can generate one from the imports used).
- Create a `RELEASE_NOTES.md` and tag v0.0.1 in git programmatically (I attempted git earlier but the environment git output was empty; I can provide commands).
- Scaffold the LSTM training notebook and a small data-prep script to start per-vessel model building.

Which of these would you like me to do next?  I will mark the README task completed in the todo list once you confirm. 