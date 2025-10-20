# Helper to send a query and update session state (used by main input and sidebar selections)

import requests
import streamlit as st
import json
import pandas


def send_query(text: str):
    try:
        r = requests.post("http://127.0.0.1:8000/query", json={"text": text}, timeout=20)
        parsed = r.json().get("parsed", {})
        resp = r.json().get("response", "No response.")
        formatted_response = r.json().get("formatted_response", "")

        # Store formatted response for display
        if formatted_response:
            resp['_formatted_text'] = formatted_response

        # log the search on server
        try:
            requests.post("http://127.0.0.1:8000/admin/log_search", params={"query": text}, timeout=3)
        except Exception:
            pass
    except Exception as e:
        parsed = {}
        resp = {"message": f"Backend request failed: {e}"}

    st.session_state.chat_history.append(("User", text))
    st.session_state.chat_history.append(("Bot", resp))
    st.session_state.last_bot_response = resp