from fastapi import FastAPI
from pydantic import BaseModel
import os

from .db_handler import MaritimeDB
from .nlp_interpreter import MaritimeNLPInterpreter
from .intent_executor import IntentExecutor

#db_path = os.path.join(os.path.dirname(__file__), "..", "src", "maritime_data.db")
#db_path = os.path.abspath(db_path)
db_path = "F:\Maritime_NLU\backend\nlu_chatbot\maritime_data.db"
db = MaritimeDB(db_path)
db.create_tables()  # ensure table exists
vessel_list = db.get_all_vessel_names()

nlp_engine = MaritimeNLPInterpreter(vessel_list=vessel_list)
executor = IntentExecutor(db)

app = FastAPI(title="Maritime Vessel Monitoring API")

class QueryRequest(BaseModel):
    text: str

@app.post("/query")
def nlp_query(request: QueryRequest):
    parsed = nlp_engine.parse_query(request.text)
    response = executor.handle(parsed)
    return {"parsed": parsed, "response": response}
