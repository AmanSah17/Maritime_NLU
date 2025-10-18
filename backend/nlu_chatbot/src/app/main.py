from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
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

# Resolve DB path relative to this file so code works on any machine
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
db_path = os.path.join(base_dir, "maritime_data.db")
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

class QueryRequest(BaseModel):
    text: str

@app.post("/query")
def nlp_query(request: QueryRequest):
    parsed = nlp_engine.parse_query(request.text)
    response = executor.handle(parsed)
    return {"parsed": parsed, "response": response}


@app.get("/vessels")
def list_vessels():
    """Return unique vessel names from the DB for frontend display/selection."""
    vessels = db.get_all_vessel_names()
    # Ensure uniqueness and predictable ordering
    unique = sorted({v for v in vessels if v and v.strip()})
    return {"vessels": unique}
