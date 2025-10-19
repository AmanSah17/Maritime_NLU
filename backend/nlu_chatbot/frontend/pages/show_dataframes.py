import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Dataframes", layout="wide")

st.title("Admin — Fetched DataFrames")
st.write("This page fetches and displays DataFrames returned by the backend for debugging and prototyping.")

backend_base = st.text_input("Backend base URL", value="http://127.0.0.1:8000")

if st.button("Show fetched dataframes"):
    with st.spinner("Fetching unique vessels..."):
        try:
            r = requests.get(f"{backend_base}/admin/unique_vessels_df", timeout=8)
            payload = r.json()
            if "error" in payload:
                st.error(payload.get("error"))
            else:
                df = pd.DataFrame(payload.get("records", []), columns=payload.get("columns", []))
                st.subheader("Unique vessels")
                st.dataframe(df)
        except Exception as e:
            st.error(f"Request failed: {e}")

    with st.spinner("Fetching sample of vessel rows..."):
        try:
            r2 = requests.get(f"{backend_base}/admin/query_df?name=all_vessels_sample", timeout=12)
            payload2 = r2.json()
            if "error" in payload2:
                st.error(payload2.get("error"))
            else:
                df2 = pd.DataFrame(payload2.get("records", []), columns=payload2.get("columns", []))
                st.subheader("Sample vessel rows (up to 500)")
                st.dataframe(df2)
        except Exception as e:
            st.error(f"Request failed: {e}")

    st.success("Fetched and displayed available dataframes.")
else:
    st.info("Click the button to fetch DataFrames from the backend. This does not change existing `app.py`.")


st.markdown("---")
st.header("LLM-assisted extraction (backend or local transformer)")
nl_query = st.text_area("Write a natural-language query to extract vessel/time identifiers:", value="show the location of +BRAVA at 10 hours 25 minutes")

col1, col2 = st.columns(2)

with col1:
    if st.button("Use backend NLU"):
        try:
            r = requests.post(f"{backend_base}/query", json={"text": nl_query}, timeout=8)
            payload = r.json()
            st.subheader("Backend parsed output")
            st.json(payload.get("parsed", {}))
            parsed = payload.get("parsed", {})
            # if parsed contains vessel or identifiers, show quick describe button
            vessel_name = parsed.get("vessel_name")
            identifiers = parsed.get("identifiers", {})
            mmsi = identifiers.get("mmsi") if identifiers else None
            if vessel_name:
                if st.button(f"Describe vessel '{vessel_name}'"):
                    r2 = requests.get(f"{backend_base}/admin/describe_vessel", params={"vessel": vessel_name}, timeout=8)
                    st.json(r2.json())
            elif mmsi:
                if st.button(f"Describe MMSI {mmsi}"):
                    r3 = requests.get(f"{backend_base}/admin/describe_vessel", params={"mmsi": mmsi}, timeout=8)
                    st.json(r3.json())
        except Exception as e:
            st.error(f"Backend NLU request failed: {e}")

    with col2:
        st.write("Backend-only NLU (spaCy); no local transformers used")
        if st.button("Use backend NLU and describe"):
            try:
                r = requests.post(f"{backend_base}/query", json={"text": nl_query}, timeout=20)
                payload = r.json()
                st.subheader("Backend parsed output")
                st.json(payload.get("parsed", {}))
                parsed = payload.get("parsed", {})
                vessel_name = parsed.get("vessel_name")
                identifiers = parsed.get("identifiers", {})
                mmsi = identifiers.get("mmsi") if identifiers else None
                if vessel_name:
                    r2 = requests.get(f"{backend_base}/admin/describe_vessel", params={"vessel": vessel_name}, timeout=10)
                    st.json(r2.json())
                elif mmsi:
                    r3 = requests.get(f"{backend_base}/admin/describe_vessel", params={"mmsi": mmsi}, timeout=10)
                    st.json(r3.json())
            except Exception as e:
                st.error(f"Backend NLU request failed: {e}")

st.markdown("""
**Notes:**
- The "Use backend NLU" button calls the FastAPI `/query` endpoint which uses the repository's NLU pipeline (spaCy + optional HF NER) — recommended for production.
- The "Run local transformer NER" option will attempt to run a local HF pipeline; this may download model weights and be slow if not cached.
""")

# SQL Index Creation (to be run in the database, not in Streamlit)
"""
CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);
CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);
"""
