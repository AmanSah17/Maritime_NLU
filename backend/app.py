# app.py
from fastapi import FastAPI
from nlp_interpreter import MaritimeNLPInterpreter

app = FastAPI(title="Maritime NLP API")

# Preload known vessel names
vessel_list = ["INS Kolkata", "MSC Flaminia", "Ever Given"]
nlp_model = MaritimeNLPInterpreter(vessel_list)

@app.post("/interpret/")
def interpret_query(payload: dict):
    query = payload.get("query", "")
    if not query:
        return {"error": "Missing query text."}
    return nlp_model.parse_query(query)
