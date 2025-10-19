from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import uuid
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

# Ensure the current `app` directory is importable when uvicorn executes the module
# This avoids "attempted relative import with no known parent package" when running
# `uvicorn app.main:app` from the src folder or similar setups.
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from db_handler import MaritimeDB
from nlp_interpreter import MaritimeNLPInterpreter
from intent_executor import IntentExecutor
import time
import logging

logging.basicConfig(level=logging.INFO)

# Resolve DB path relative to this file so code works on any machine
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# Allow overriding the DB file via environment for testing smaller subsets
default_db = os.path.join(base_dir, "maritime_data.db")
db_path = os.environ.get("BACKEND_DB_PATH", default_db)
db = MaritimeDB(db_path)
db.create_tables()  # ensure table exists
vessel_list = db.get_all_vessel_names()

nlp_engine = MaritimeNLPInterpreter(vessel_list=vessel_list)
executor = IntentExecutor(db)

app = FastAPI(title="Maritime Vessel Monitoring API")

# allow origins for development frontends (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: serve React build static files if present under frontend-react/build
from fastapi.staticfiles import StaticFiles
react_build = os.path.join(base_dir, 'frontend-react', 'build')
if os.path.isdir(react_build):
    app.mount('/', StaticFiles(directory=react_build, html=True), name='react')

# job executor and registry
executor_pool = ThreadPoolExecutor(max_workers=4)
jobs = {}

class QueryRequest(BaseModel):
    text: str


class JobRequest(BaseModel):
    vessel: str | None = None
    mmsi: int | None = None
    limit: int = 1000
    end_dt: str | None = None


@app.post("/query")
async def nlp_query(request: QueryRequest):
    # Keep parsing synchronous (spaCy) but the endpoint is async-friendly to allow DB async calls
    parsed = nlp_engine.parse_query(request.text)
    # executor may call DB; allow it to run (it will use sync DB unless refactored)
    response = executor.handle(parsed)
    return {"parsed": parsed, "response": response}


@app.get("/health")
def health_check():
    return {"ok": True}


@app.get("/vessels")
def list_vessels():
    """Return unique vessel names from the DB for frontend display/selection."""
    # legacy endpoint — avoid returning all names for very large DBs; prefer /vessels/search
    vessels = db.get_all_vessel_names()
    unique = sorted({v for v in vessels if v and v.strip()})
    return {"vessels": unique}


@app.get("/vessels/search")
async def search_vessels(q: str, limit: int = 50):
    """Search vessel names by prefix (fast, limited) to avoid loading full list into frontend."""
    names = db.search_vessels_prefix(q, limit=limit)
    return {"vessels": names}


@app.on_event("startup")
def ensure_search_log_table():
    # create a small table to log user searches (non-critical)
    try:
        create_sql = "CREATE TABLE IF NOT EXISTS search_log (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, ts TEXT);"
        if getattr(db, "engine", None) is not None:
            # use engine
            from sqlalchemy import text
            with db.engine.begin() as conn:
                conn.execute(text(create_sql))
        else:
            db.conn.execute(create_sql)
            db.conn.commit()
    except Exception:
        pass


@app.post("/admin/log_search")
def admin_log_search(query: str):
    try:
        if getattr(db, "engine", None) is not None:
            from sqlalchemy import text
            with db.engine.begin() as conn:
                conn.execute(text("INSERT INTO search_log (query, ts) VALUES (:q, datetime('now'))"), {"q": query})
        else:
            db.conn.execute("INSERT INTO search_log (query, ts) VALUES (?, datetime('now'))", (query,))
            db.conn.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/admin/recent_searches")
def admin_recent_searches(limit: int = 50):
    try:
        query = "SELECT query, ts FROM search_log ORDER BY ts DESC LIMIT %s" % int(limit)
        if getattr(db, "engine", None) is not None:
            df = pd.read_sql_query(query, con=db.engine)
        else:
            df = pd.read_sql_query(query, con=db.conn)
        records = df.to_dict(orient="records")
        return {"records": records}
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/unique_vessels_df")
def admin_unique_vessels_df():
    """Return the unique vessels DataFrame as JSON for frontend admin pages.
    This is intentionally a read-only diagnostics endpoint used by the Streamlit 'pages' view.
    """
    df = db.get_unique_vessels_df()
    return {"columns": df.columns.tolist(), "records": df.to_dict(orient="records")}


@app.get("/admin/query_df")
def admin_query_df(name: str = ""):
    """Run a small set of pre-defined dataframe queries by name and return results.
    executor_pool = ThreadPoolExecutor(max_workers=4)
    jobs = {}

    Supported names:
      - unique_vessels
      - all_vessels_sample
    """
    if name == "unique_vessels":
        df = db.get_unique_vessels_df()
    elif name == "all_vessels_sample":
        # return a small sample of all vessel rows
        df = db.fetch_by_time_range("1970-01-01 00:00:00", "2099-12-31 23:59:59", limit=500)
    else:
        return {"error": "unsupported query name"}

    return {"columns": df.columns.tolist(), "records": df.to_dict(orient="records")}


@app.get("/admin/describe_vessel")
def admin_describe_vessel(vessel: str = None, mmsi: int = None, limit: int = 10, end_dt: str = None):
    """Return identifiers and a short recent track for a vessel given a name or MMSI.

    Example: /admin/describe_vessel?vessel=+BRAVA
             /admin/describe_vessel?mmsi=123456789
              /admin/describe_vessel?vessel=BRAVA&end_dt=2023-01-01T00:00:00
    """
    start = time.time()
    target_dt = end_dt if end_dt else "2099-12-31 23:59:59"
    if vessel:
        # try to fetch last known row
        logging.info(f"describe_vessel: fetching by name={vessel} limit={limit}")
        df = db.fetch_vessel_by_name_at_or_before(vessel, target_dt)
        track = db.fetch_track_ending_at(vessel_name=vessel, end_dt=target_dt, limit=limit)
    elif mmsi:
        logging.info(f"describe_vessel: fetching by mmsi={mmsi} limit={limit}")
        df = db.fetch_vessel_by_mmsi_at_or_before(int(mmsi), target_dt)
        track = db.fetch_track_ending_at(mmsi=int(mmsi), end_dt=target_dt, limit=limit)
    else:
        return {"error": "provide vessel name or mmsi"}

    info = {}
    if not df.empty:
        row = df.iloc[0].to_dict()
        info.update({
            "mmsi": int(row.get("MMSI")) if row.get("MMSI") is not None else None,
            "call_sign": row.get("CallSign"),
            "vessel_name": row.get("VesselName"),
        })
    dur = time.time() - start
    logging.info(f"describe_vessel completed in {dur:.3f}s")
    # return track as list of records
    return {"identifiers": info, "track": track.to_dict(orient="records"), "took_seconds": dur}

def _run_long_describe(params):
    try:
        vessel = params.get("vessel")
        mmsi = params.get("mmsi")
        limit = params.get("limit", 1000)
        end_dt = params.get("end_dt") or "2099-12-31 23:59:59"
        if vessel:
            df = db.fetch_vessel_by_name_at_or_before(vessel, end_dt)
            track = db.fetch_track_ending_at(vessel_name=vessel, end_dt=end_dt, limit=limit)
        elif mmsi:
            df = db.fetch_vessel_by_mmsi_at_or_before(int(mmsi), end_dt)
            track = db.fetch_track_ending_at(mmsi=int(mmsi), end_dt=end_dt, limit=limit)
        else:
            return {"error": "provide vessel or mmsi"}

        info = {}
        if not df.empty:
            row = df.iloc[0].to_dict()
            info.update({
                "mmsi": int(row.get("MMSI")) if row.get("MMSI") is not None else None,
                "call_sign": row.get("CallSign"),
                "vessel_name": row.get("VesselName"),
            })

        return {"identifiers": info, "track": track.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/submit_query_job")
def submit_query_job(job: JobRequest):
    """Submit a background describe job.

    Accepts a JSON body with fields: vessel, mmsi, limit, end_dt.
    Returns a job_id which can be polled via /admin/job_status/{job_id}.
    """
    vessel = job.vessel
    mmsi = job.mmsi
    limit = int(job.limit or 1000)
    end_dt = job.end_dt

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "PENDING", "result": None, "error": None}

    def _task():
        jobs[job_id]["status"] = "RUNNING"
        try:
            res = _run_long_describe({"vessel": vessel, "mmsi": mmsi, "limit": limit, "end_dt": end_dt})
            jobs[job_id]["result"] = res
            jobs[job_id]["status"] = "DONE"
        except Exception as e:
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["status"] = "FAILED"

    executor_pool.submit(_task)
    return {"job_id": job_id}


@app.get("/admin/job_status/{job_id}")
def job_status(job_id: str):
    if job_id not in jobs:
        return {"error": "unknown job id"}
    return jobs[job_id]
