# main_query_engine.py
from db_handler import MaritimeDB
from nlp_interpreter import MaritimeNLPInterpreter
from intent_executor import IntentExecutor

def process_natural_query(query: str):
    # 1️⃣ Connect to DB
    db = MaritimeDB("backend\nlu_chatbot\maritime_data.db")

    # 2️⃣ Load vessel names
    vessel_list = db.get_all_vessel_names()

    # 3️⃣ Initialize NLP engine
    nlp_engine = MaritimeNLPInterpreter(vessel_list=vessel_list)
    parsed = nlp_engine.parse_query(query)
    print("🔍 Parsed Query:", parsed)

    # 4️⃣ Execute Intent
    executor = IntentExecutor(db)
    response = executor.handle(parsed)
    return response


if __name__ == "__main__":
    queries = [
        "Show the last known position of INS Kolkata.",
        "Predict where MSC Flaminia will be after 30 minutes.",
        "Check if the latest position of Ever Given is consistent with its past movement.",
    ]

    for q in queries:
        print("\n🗣️ Query:", q)
        print("💬 Response:", process_natural_query(q))
